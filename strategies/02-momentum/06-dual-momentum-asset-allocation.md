# Dual Momentum (Relative + Absolute) Asset Allocation

## 1. Classification

- **Category:** Momentum (asset-allocation level, long-only)
- **Asset classes:** Asset-class ETFs/futures: equities (regions), bonds, cash; extensible to gold/commodities/crypto
- **Style:** Long-only rotation with cash fallback
- **Horizon:** Monthly decisions, holdings for months
- **Capacity:** Very high
- **Complexity:** Very low; **Data burden:** monthly total returns for a handful of indices — the lightest in this corpus

## 2. Economic rationale

Combines the two momentum findings at the asset-class level: **relative momentum** (hold the recently-stronger of two similar assets — e.g., US vs international equities) and **absolute momentum** (hold equities only if their trailing excess return over cash is positive; otherwise hold bonds/cash). The relative leg harvests cross-asset underreaction; the absolute leg is time-series momentum functioning as a **bear-market circuit breaker** — it exits risk assets after sustained downtrends, which historically avoided the bulk of 2000–02 and 2008 drawdowns. Counterparty/mechanism: same slow-flow and underreaction stories as CS/TS momentum, applied to the largest, slowest-moving allocation decisions (institutional asset allocation moves over quarters). This is TSMOM economics packaged for a long-only, low-maintenance implementation — included as a distinct doc because the *construction* (binary rotation, cash fallback, no shorting, no leverage) makes it deployable where futures strategies aren't.

## 3. Signal & rules specification

Antonacci GEM baseline [M8]:

- **Instruments:** US equities (e.g., S&P 500 fund), international ex-US equities, aggregate bonds, T-bills (cash proxy).
- **Monthly, at month-end:**
  1. Absolute filter: compute 12-month total return of US equities minus T-bill return. If positive → risk-on; else → hold bonds.
  2. Relative selection (risk-on only): hold whichever of US / international equities has the higher 12-month return. 100% in the selected asset.
- **Parameter ranges:** lookback 6–12 months (12 canonical; average of 3/6/12 more robust); holdings can be split top-2-of-N for a larger menu; trade a few days after month-end to avoid month-turn crowding.
- **Extensions to test:** add gold/commodity/REIT/crypto sleeves with the same dual filter per sleeve; vol-weighted blends instead of 100% winner-take-all (reduces switch-timing luck).
- No leverage, no shorts; whole portfolio turns over a few times a year at most.

## 4. Evidence & key research

- Antonacci [M8]: GEM 1974–2013 ~17.4% ann. vs ~12.2% for buy-and-hold ACWI with max DD −22.7% vs −60% (his sample; monthly data).
- The engine is MOP TSMOM [M3] + cross-asset relative momentum [M2] — evidence base inherited from those (strong).
- Out-of-sample reality check: 2015–2025 live-era results for GEM-style rules were mediocre — whipsawed in 2015–16, late exit/late re-entry around COVID (March 2020 exit near lows, missed the V-recovery), and lagged the US bull badly when signals sat in international/bonds. Ann. returns trailed S&P by several points over the 2010s. This is the documented cost of the circuit breaker in V-shaped regimes; it paid in 2000–02/2008-type extended bears, which haven't recurred since publication.
- **Decay status:** premium inherits TSMOM's modest decay; the *insurance property* is regime-dependent, not dead — but a 2010s-style melt-up is its worst case.

## 5. Expected performance profile

- Long-run expectation: **equity-like returns with roughly half the max drawdown**, at the price of lagging in uninterrupted bull markets and whipsaw losses at sharp reversals.
- Net Sharpe: ~0.5–0.7 long-run (vs ~0.4–0.5 buy-and-hold); tracking error to equities is huge (10%+) — behavioral tolerance is the real constraint.
- Skew: reduces left tail at multi-month horizon; adds "reversal risk" (out during rebounds).
- Turnover/costs: trivial (3–6 switches/yr, liquid ETFs).

## 6. Failure modes & risks

- **V-shaped crashes** (2020): exit after the fall, re-enter after the rise — pays the insurance premium and receives nothing.
- Whipsaw clusters (2015–16, 2018-Q4): several false exits per year each costing 1–3%.
- Concentration: 100% single-asset holdings — model/execution errors are total-portfolio events; the top-2 or vol-blend variants mitigate.
- Tax: switching realizes gains (relevant for taxable accounts).

## 7. Backtesting guidance

- Use **total-return** index data (dividends), monthly; signals from month-end closes, execution at next-day close with costs.
- Extend history before ETFs with index series (available to 1970s) — but apply expense-ratio-equivalent drags.
- The essential honesty test: report published-sample (pre-2014) and live-era (2014→) separately; the strategy's case rests on long-history bear protection, so also run 1929–1950 with proxy data if possible.
- Whipsaw sensitivity: count and cost the false-exit episodes; test lookback averaging vs single-lookback (robustness, not optimization).
- Compare against: buy-and-hold, 60/40, and a simple 10-month moving-average timing rule (the Faber baseline) — dual momentum must beat these to justify itself.

## 8. Recommendations for use

- **Backtest priority: medium.** Trivial to implement, and it's the right *first* backtest to shake down data pipelines end-to-end before harder projects.
- Best fit: tax-advantaged, low-maintenance capital that needs drawdown control without shorting/derivatives — i.e., a personal-capital sleeve, not the fund's alpha engine.
- If futures infrastructure exists, full TSMOM (doc 02) dominates it; don't run both as separate risk allocations.
