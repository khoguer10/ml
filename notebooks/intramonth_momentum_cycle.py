"""
The Intramonth Momentum Cycle - Nathan, Suominen & Tasa (2026), PDFs/ssrn-6426026.pdf

Reproduces the paper's central decomposition on a synthetic panel: momentum
(Winners-Minus-Losers) returns concentrate in the six-day PreTOM window
[tau-9, tau-4] that ends four trading days before month-end, and the effect is
driven by losers underperforming the market during that window.

The bundled data/sp500.json covers only ~1 year, which is too short for a 12-2
momentum formation, so - like notebooks/mvp.py and marcenko_pastur_random.py -
this demo builds a synthetic multi-year cross-section. The same src/momentum.py
functions run unchanged on real CRSP-style price/cap panels.
"""

import numpy as np
import pandas as pd

from src.momentum import (
    momentum_signal,
    assign_deciles,
    daily_deciles,
    window_labels,
    decile_returns,
    wml_returns,
    decompose_windows,
    market_adjusted_leg,
)


def simulate_panel(n_assets=200, years=25, seed=0, drag=0.0030):
    """Synthetic daily prices where the loser drag is concentrated in PreTOM.

    The paper's point is that losers do not drift down every day - they get sold
    for liquidity in the six-day PreTOM window. So returns are pure noise on Rest
    days, and on PreTOM days the current trailing-losers (bottom decile) take an
    extra negative return ``drag``. This is self-reinforcing: the names dragged
    down keep ranking as losers, so a 12-2 momentum sort recovers the same cohort
    and the WML spread loads almost entirely on PreTOM, with Rest near zero.
    """
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range('2000-01-03', periods=years * 252)
    is_pretom = (window_labels(dates) == 'PreTOM').values

    prices = np.zeros((len(dates), n_assets))
    prices[0] = 100.0
    trailing = rng.normal(0, 0.05, n_assets)    # initial ~1yr performance proxy

    for t in range(1, len(dates)):
        ret = rng.normal(0, 0.008, n_assets)    # idiosyncratic noise, no drift
        if is_pretom[t]:
            losers = trailing <= np.quantile(trailing, 0.10)
            ret[losers] -= drag                 # month-end liquidity selling
        prices[t] = prices[t - 1] * (1 + ret)
        trailing = 0.985 * trailing + ret       # decaying trailing performance

    cols = [f'A{i:03d}' for i in range(n_assets)]
    return pd.DataFrame(prices, index=dates, columns=cols)


def main():
    pd.set_option('display.width', 120)
    pd.set_option('display.max_columns', None)
    prices = simulate_panel()

    # form fixed monthly 12-2 momentum deciles, held within each calendar month
    signal = momentum_signal(prices, lookback=12, skip=1)
    monthly_dec = assign_deciles(signal, n=10)
    dec = daily_deciles(monthly_dec, prices.index)

    # daily decile returns (equal-weighted here; pass weights= for value weights)
    dret = decile_returns(prices, dec, n=10)
    wml = wml_returns(dret, n=10)

    labels = window_labels(prices.index)
    decomp = decompose_windows(wml, labels)

    print('=== WML decomposition by calendar window ===')
    print(decomp.round(4))

    print('\n=== Losers (D1) minus market, bps/day ===')
    print(market_adjusted_leg(dret, labels, leg=1).round(2))

    pretom_g = decomp.loc['PreTOM', 'growth_of_$1']
    rest_g = decomp.loc['Rest', 'growth_of_$1']
    print(f'\nGrowth of $1: PreTOM-only = {pretom_g:.2f}  vs  Rest-only = {rest_g:.2f}')
    print('(Paper, 1980-2025 value-weighted: $18.78 vs $2.37.)')


if __name__ == '__main__':
    main()
