# How the Intramonth Momentum Cycle idea was built

A reverse-engineering of the *reasoning process* behind Nathan, Suominen & Tasa
(2026), *The Intramonth Momentum Cycle* (`PDFs/ssrn-6426026.pdf`), written as a
reusable template for generating similar anomaly-mechanism ideas. This is not a
summary of the findings (see `src/momentum.py` and
`notebooks/intramonth_momentum_cycle.py` for the implementation) — it is a map of
the *moves* that turned a 30-year-old open puzzle into a sharp, falsifiable claim.

---

## The reasoning chain, step by step

### 0. Start from a big anomaly with no consensus
Momentum is "the most pervasive anomaly in financial markets" and, per Fama's own
Nobel lecture, "the biggest challenge to market efficiency." Three decades in,
the literature is still split between behavioral (under-reaction) and risk-based
stories. **No consensus = room for a new mechanism.** The authors did not invent a
new anomaly; they picked the most-studied one precisely because its *cause* was
still contested.

> Template move: target a famous, well-measured effect whose *why* is unsettled,
> not an obscure one whose *existence* is in doubt.

### 1. Re-slice along an orthogonal axis nobody decomposes
The entire literature asks *why* momentum exists. The authors instead asked
*when* it is earned — they indexed every trading day by its position **relative to
month-end** (τ = last trading day) and compounded WML returns by calendar
position. Result: **78% of cumulative WML return is earned in a six-day window
[τ−9, τ−4] that is only ~29% of trading days** ($18.78 vs $2.37 from $1, 1980–2025).

> Template move: take a return series everyone studies cross-sectionally and cut
> it on a *time/calendar* axis they treat as noise (time-of-month, time-of-day,
> day-of-week, around index rebalances or expiries). Concentration is a clue.

### 2. Localize the effect — which leg carries it?
Decomposing WML into market-adjusted legs showed the concentration is **entirely
loser-driven**: losers underperform the market by ≈ −7.9 bps/day in the window and
≈ 0 otherwise; winners show no comparable timing. The phenomenon shrank from "a
momentum puzzle" to "a *loser-selling* puzzle in *six specific days*."

> Template move: never stop at the spread. Split into legs and subsets until the
> effect lives in the smallest possible box — that box names the mechanism.

### 3. Map the localized pattern onto exogenous real-world "plumbing"
The window did not come from data-mining — it was **borrowed**. Etula et al. (2020)
had already documented pre-turn-of-the-month price pressure from institutions'
**month-end liquidity needs**. The authors asked a single connecting question:
*does that known month-end selling pressure fall on momentum losers?* This grafts
an externally-validated mechanism onto the new fact, and (crucially) the window is
pre-specified by prior work rather than fitted.

> Template move: look for an institutional/market-structure process (settlement,
> fund flows, tax dates, index rebalancing, options expiry, margin cycles) whose
> *timing* already matches your concentration. Reuse its window; don't fit one.

### 4. Name a unifying mechanism that absorbs rival micro-stories
Rather than pick one reason losers get sold, they introduced **"asset
dispensability"** — a single concept unifying three previously-separate selling
motives: (i) embedded losses → tax-loss harvesting, (ii) low/zero dividends → little
foregone income when liquidated, (iii) salience under time pressure → managers
heuristically dump the obvious underperformers. Losers score high on all three, so
they are what you sell first to raise cash.

> Template move: when several known stories each explain part of your subset,
> coin one latent trait that makes them facets of the same thing. A name turns a
> list of correlations into a mechanism — and yields new predictions (Step 5b).

### 5. Derive predictions only *this* mechanism makes, then test them
This is where an interesting correlation becomes a defended causal claim. Each test
is chosen because rival explanations do **not** predict it.

- **5a. Direct evidence of the channel.** If it's liquidity selling, signed trade
  data should show net *selling* pressure on losers concentrated in PreTOM — and
  it's strongest in *liquid* losers (you sell what's cheap to sell). Confirmed in
  TAQ order-imbalance and mutual-fund flow data.
- **5b. A better proxy must work better.** If the driver is *dispensability* and
  not the 12-2 sort itself, a sort that proxies dispensability more directly should
  show an even larger window premium. The **52-week-high** sort (more directly
  embedded-loss / non-payer aligned) yields **$45.72** in PreTOM vs $18.78 for WML —
  same six-day timing, bigger magnitude. The mechanism, not the specific ranking,
  is doing the work.
- **5c. Transitory pressure must reverse.** Price pressure ≠ news, so the loser gap
  should partially unwind afterward. ≈ 70% reverses in the Post window [τ−3, τ+3].
- **5d. The clincher — a natural experiment.** The mechanism makes a *mechanical*
  prediction about timing: shortening the settlement cycle lets investors raise
  settled cash one day later, so the marginal selling day moves one trading day
  **closer to month-end** (T+3→T+2 moves τ−5→τ−4; T+2→T+1 moves τ−4→τ−3). The
  identifying test is the *relative shift of two adjacent boundary days*, which no
  behavioral or risk story implies. Verified across the 2024 US T+1 reform, the
  2014 synchronized European T+2 reform, and the 2017 US T+2 reform — with placebo
  days and false reform dates returning nulls.

> Template move: rank candidate tests by how *uniquely* your mechanism predicts
> them. Prize any prediction tied to an exogenous rule change — a rule change is a
> free natural experiment that behavioral/risk priced-factor stories can't fake.

### 6. Actively kill the alternatives
The mechanism is argued by *elimination*, not just confirmation:
- **Tax-loss harvesting alone?** No — the effect survives excluding quarter-ends and
  December (−7.0 bps, basically unchanged).
- **Benchmark/passive rebalancing?** Wrong sign and direction.
- **Momentum crash risk** (Barroso–Santa-Clara)? The *profit* window (PreTOM) and the
  *crash* window (month-start) are distinct, so crash-avoidance can't be the source.

> Template move: list the obvious rival explanations *before* you publish and design
> the one robustness cut that each would fail. Refutation > accumulation.

### 7. Establish external validity
Same loser-asymmetric, PreTOM-concentrated pattern in **19 developed markets** and in
three acute fund-outflow episodes (Sep/Oct 2008, Mar 2020), plus a re-reading of
Carhart UMD fund persistence as a PreTOM phenomenon. Replication across independent
samples guards against an in-sample fluke.

### 8. Let the idea spawn an agenda
The closing generalization: *many* cross-sectional anomalies share a short leg of
dispensable stocks, so "a portion of cross-sectional return predictability may turn
out to be a settlement-cycle phenomenon." A good mechanism doesn't just explain one
fact — it predicts where to look next.

---

## The template, abstracted

1. **Pick** a big, well-measured anomaly whose *cause* is contested.
2. **Re-slice** it on a calendar/time axis the field ignores; look for concentration.
3. **Localize** to the smallest leg/subset that still carries the effect.
4. **Match** that localized timing to an exogenous market-plumbing process; reuse its
   pre-existing window rather than fitting one.
5. **Name** a latent trait that unifies the competing micro-explanations.
6. **Derive** predictions your mechanism makes *uniquely* — especially ones tied to a
   rule change / natural experiment — and test them.
7. **Refute** each rival explanation with a targeted cut.
8. **Replicate** across markets and regimes.
9. **Generalize** the mechanism into a research agenda.

## Guards against fooling yourself (built into the paper)
- The window is **pre-specified** from Etula et al. (2020), not fitted — avoids the
  classic "search for the best window" data-mining trap.
- A **within-month permutation test** confirms PreTOM is the deepest loser trough
  (p = 0.012), quantifying the chance the concentration is luck.
- The headline identification is a **difference-in-differences on a settlement
  reform** with placebo days/dates — the cleanest available stand-in for a randomized
  experiment in this setting.

## Applying it to this repo
The same lens fits the methods already here:
- The **triple-barrier** labels (`src/labeling.py`) define *when* an outcome is
  realized — a natural place to ask whether label outcomes cluster by calendar
  position (Step 2) before treating them as i.i.d.
- The **PreTOM / Rest / Post** window labeler (`src/momentum.py: window_labels`) is
  reusable as the "orthogonal time axis" of Step 1 for *any* daily strategy in this
  repo — drop a signal in, decompose its P&L by window, and check for concentration.
