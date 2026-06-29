"""
The Intramonth Momentum Cycle
Daniel Nathan, Matti Suominen, Joni Tasa (2026), SSRN-6426026 (PDFs/ssrn-6426026.pdf).

The paper shows that U.S. equity momentum (Winners-Minus-Losers) returns
concentrate in a six-trading-day window each month that ends four trading days
before month-end ("PreTOM"). Over 1980-2025, $1 in the value-weighted WML
strategy grows to $18.78 during those six days versus $2.37 during the rest of
the month, and the asymmetry is driven by losers underperforming the market.

This module implements the mechanical building blocks of that result:

  * momentum_signal      - 12-2 cumulative-return momentum (skip most recent month)
  * assign_deciles       - cross-sectional decile sort, fixed monthly
  * daily_deciles        - expand monthly decile assignments to daily frequency
  * tom_offset           - trading-day index relative to the turn-of-the-month tau
  * window_labels        - classify each day as PreTOM / Rest / Post
  * decile_returns       - per-decile daily returns (equal- or value-weighted)
  * wml_returns          - daily D10 - D1 spread
  * decompose_windows    - growth of $1 and bps/day, split by calendar window

Prices are a wide DataFrame indexed by a sorted DatetimeIndex of trading days
with one column per asset. Market caps, when supplied for value weighting, share
the same shape.
"""

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Momentum signal and decile assignment
# ---------------------------------------------------------------------------

def momentum_signal(prices, lookback=12, skip=1):
    """Fixed monthly 12-2 momentum signal.

    For holding month m the signal is the cumulative return over months
    [m - lookback, m - skip - 1], i.e. the trailing ``lookback``-month return
    that skips the most recent ``skip`` month(s). With the paper's defaults
    (lookback=12, skip=1) this is the cumulative return over months -12 through
    -2, computed from month-end prices.

    Returns a month-end indexed DataFrame whose row at month m is the signal
    used to form deciles that are then held throughout month m.
    """
    monthly = prices.resample('ME').last()
    # close(m - skip - 1) / close(m - lookback - 1) - 1
    end = monthly.shift(skip + 1)
    start = monthly.shift(lookback + 1)
    return end / start - 1.0


def assign_deciles(signal, n=10):
    """Cross-sectional sort of each row of ``signal`` into ``n`` deciles.

    Decile 1 (D1) is the bottom group (losers); decile ``n`` (D10) is the top
    group (winners). Rows are ranked independently, so the sort is repeated
    fresh each formation month. Assets with a missing signal stay NaN.
    """
    def _rank_row(row):
        valid = row.dropna()
        if len(valid) < n:
            return pd.Series(np.nan, index=row.index)
        # qcut on rank breaks ties deterministically; labels 1..n
        bins = pd.qcut(valid.rank(method='first'), n, labels=range(1, n + 1))
        return bins.reindex(row.index).astype(float)

    return signal.apply(_rank_row, axis=1)


def daily_deciles(monthly_deciles, daily_index):
    """Expand month-end decile assignments to a daily DatetimeIndex.

    A sort formed at the end of month m is held constant through every trading
    day of month m, matching the paper's fixed monthly sorts. The assignment
    formed at the end of month m-1 governs month m's returns, so we shift the
    monthly assignments forward by one month before broadcasting to days.
    """
    held = monthly_deciles.shift(1)
    held.index = held.index.to_period('M')
    days_period = daily_index.to_period('M')
    out = held.reindex(days_period)
    out.index = daily_index
    return out


# ---------------------------------------------------------------------------
# Turn-of-the-month calendar windows
# ---------------------------------------------------------------------------

def tom_offset(index):
    """Trading-day offset of each date relative to its month-end tau.

    tau (the last trading day of the month) has offset 0; the previous trading
    day is -1, and so on. Offsets are always non-positive because they count
    backward from month-end within the same calendar month.
    """
    index = pd.DatetimeIndex(index)
    months = index.to_period('M')
    # 0 = last trading day of the month, 1 = previous, ...
    rank_from_end = pd.Series(index, index=index).groupby(months).cumcount(
        ascending=False)
    return -rank_from_end


def window_labels(index, pretom=(-9, -4), post=(-3, 3)):
    """Label each trading day PreTOM / Rest / Post relative to month-end.

    PreTOM is the six-day window [tau-9, tau-4] (inclusive). Post is the
    seven-day window [tau-3, tau+3] around month-end. Rest is everything that
    is not PreTOM. PreTOM days all fall inside their own calendar month, so the
    within-month backward offset is sufficient to identify them; Post spans the
    month boundary and is reported separately for the reversal analysis.

    Returns a string Series aligned to ``index`` with values in
    {'PreTOM', 'Post', 'Rest'}: a day is PreTOM if it lies in [tau-9, tau-4],
    else Post if it lies in the [tau-3, tau+3] band around month-end, else Rest.
    PreTOM takes precedence where the bands would otherwise overlap.
    """
    index = pd.DatetimeIndex(index)
    offset = tom_offset(index)

    label = pd.Series('Rest', index=index)
    in_pretom = (offset >= pretom[0]) & (offset <= pretom[1])
    label[in_pretom] = 'PreTOM'

    # Post = [tau-3, tau+3]: the tau-3..tau-0 leg uses the current month's
    # offset; the tau+1..tau+3 leg is the first few trading days of the next
    # month. We mark both legs without overriding PreTOM.
    in_post_left = (offset >= post[0]) & (offset <= 0)
    # first ``post[1]`` trading days of each month are tau+1..tau+post[1]
    rank_from_start = pd.Series(index, index=index).groupby(
        index.to_period('M')).cumcount()
    in_post_right = rank_from_start < post[1]
    in_post = (in_post_left | in_post_right) & ~in_pretom
    label[in_post] = 'Post'
    return label


# ---------------------------------------------------------------------------
# Portfolio returns
# ---------------------------------------------------------------------------

def decile_returns(prices, deciles, weights=None, n=10):
    """Daily return of each momentum decile.

    For every day and decile the constituent stock returns are aggregated. With
    ``weights=None`` the aggregation is equal-weighted; otherwise ``weights`` is
    a DataFrame of market caps (same shape as ``prices``) and the paper's
    convention applies: previous-day caps, normalized to sum to one within each
    (day, decile) cell.

    Returns a DataFrame indexed by date with columns 1..n (the deciles) plus
    'mkt' (the value-weighted market return across all assets with a decile).
    """
    rets = prices.pct_change()
    # align decile assignments to the return dates
    dec = deciles.reindex(rets.index)

    if weights is None:
        w = pd.DataFrame(1.0, index=rets.index, columns=rets.columns)
    else:
        w = weights.reindex_like(rets).shift(1)
    w = w.where(dec.notna())

    out = pd.DataFrame(index=rets.index)
    for d in range(1, n + 1):
        mask = dec == d
        ww = w.where(mask)
        norm = ww.div(ww.sum(axis=1), axis=0)
        out[d] = (rets * norm).sum(axis=1, min_count=1)

    # market = value-weighted (or equal-weighted) return over all ranked names
    wm = w.div(w.sum(axis=1), axis=0)
    out['mkt'] = (rets * wm).sum(axis=1, min_count=1)
    return out


def wml_returns(decile_rets, n=10):
    """Daily Winners-Minus-Losers spread: D(n) - D1."""
    return decile_rets[n] - decile_rets[1]


# ---------------------------------------------------------------------------
# Calendar-window decomposition
# ---------------------------------------------------------------------------

def growth_of_dollar(daily_returns):
    """Compound a daily-return series into the growth of $1 (final value)."""
    return float((1.0 + daily_returns.dropna()).prod())


def decompose_windows(wml, labels):
    """Split the WML series by calendar window and summarize each.

    Mirrors the paper's portfolio-level decomposition: a self-financing strategy
    that only takes the WML position on the relevant window's days (holding cash
    elsewhere). Returns a DataFrame indexed by window with the growth of $1, the
    mean daily return in basis points, the number of days, and the share of the
    full-sample cumulative WML return earned in that window.
    """
    wml = wml.dropna()
    labels = labels.reindex(wml.index)
    total_log = np.log1p(wml).sum()

    rows = {}
    for win in ['PreTOM', 'Rest', 'Post']:
        r = wml[labels == win]
        if r.empty:
            continue
        rows[win] = {
            'growth_of_$1': growth_of_dollar(r),
            'mean_bps_per_day': r.mean() * 1e4,
            'days': int(r.shape[0]),
            'share_of_days': r.shape[0] / wml.shape[0],
            'share_of_cum_return': np.log1p(r).sum() / total_log if total_log else np.nan,
        }
    return pd.DataFrame(rows).T


def market_adjusted_leg(decile_rets, labels, leg=1):
    """Mean market-adjusted return (bps/day) of one decile by window.

    With ``leg=1`` this reproduces the paper's headline loser statistic: D1
    minus the market, averaged within PreTOM versus Rest (losers underperform
    the market by ~7.9 bps/day during PreTOM).
    """
    adj = (decile_rets[leg] - decile_rets['mkt']).dropna()
    labels = labels.reindex(adj.index)
    return pd.Series({
        win: adj[labels == win].mean() * 1e4
        for win in ['PreTOM', 'Rest', 'Post']
    }, name='bps_per_day')
