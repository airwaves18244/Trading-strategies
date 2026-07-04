# Cross-Asset Value (Long-Run Reversal to Fair Value)

## 1. Classification

- **Category:** Value / fundamental factor (macro cross-asset)
- **Asset classes:** Country equity indices, government bonds, currencies, commodities — via futures/forwards/ETFs
- **Style:** Cross-sectional within each asset class; slow
- **Horizon:** Rebalance monthly; signal horizon 1–5 years
- **Capacity:** Very high
- **Complexity:** Medium; **Data burden:** futures/index prices + valuation anchors (CAPE/yields, PPP/REER, real yields, long-run real commodity prices)

## 2. Economic rationale

Value generalizes beyond single stocks: **assets trading cheap relative to a slow-moving fundamental anchor outperform expensive ones over multi-year horizons** [M2]. Per class: country equities — low cyclically-adjusted valuation (CAPE-type) vs peers; currencies — undervalued on PPP/real-exchange-rate measures; bonds — high real yields vs peers; commodities — price low vs long-run real average (5-year reversal as proxy). Mechanism mirrors equity value: multi-year over-extrapolation of macro narratives ("Japan is over", "the dollar always wins") followed by mean reversion of expectations; plus genuine risk premia (cheap countries/currencies carry real macro fear). Counterparty: trend-extrapolating global allocators and home-biased capital ignoring relative price. Cross-asset value is *negatively correlated with cross-asset momentum/trend* — its role in the corpus is explicitly to be the other blade of the scissors [M2].

## 3. Signal & rules specification

Per-asset-class value measures (z-scored cross-sectionally within class):

- **Country equities (15–25 index futures/ETFs):** CAPE or trailing composite (E/P, D/P, B/P) relative to the country's own history and to peers; long cheapest quartile, short richest.
- **FX (G10 + liquid EM):** real effective exchange rate vs 10–20y average (PPP deviation); long undervalued, short overvalued.
- **Bonds (8–15 markets):** real yield (nominal − expected/trailing inflation) cross-sectionally; long high-real-yield, short low.
- **Commodities:** negative of past 5-year return (long-run reversal, the Asness convention) or price vs 10y real average; long the depressed, short the extended.
- **Aggregation:** equal-risk across the four class sleeves; within class, rank-weighted or top/bottom-third portfolios, inverse-vol sized; **portfolio vol target 8–10%**.
- **Rebalance:** monthly (turnover is naturally tiny); positions drift for years.
- **Blend note:** production form combines with cross-asset momentum 50/50 (value-and-momentum-everywhere construction) — the single-sleeve version exists for research clarity.

## 4. Evidence & key research

- Asness, Moskowitz & Pedersen [M2]: value premia in every asset class tested; cross-asset value Sharpe ~0.6–0.8 gross in-sample; near-zero correlation across class sleeves, negative correlation to momentum everywhere.
- Related literatures per class: CAPE country rotation (Shiller/Barclays applications; Keimling/StarCapital studies — cheap-CAPE countries outperformed over 5–10y windows historically); PPP reversion (documented at 3–5y half-lives); real-yield bond selection (Ilmanen [X4]).
- Post-publication: the 2010s were hard (US/growth/dollar dominance = one long anti-value macro regime); non-US cheapness kept getting cheaper. 2022+ partially vindicated (value across assets revived). Same structural argument as equity value: spreads widened rather than the relation dying.
- **Decay status: moderate-with-cyclical-defense;** slow signals decay slowest [X1 pattern: low-turnover anomalies decay less].

## 5. Expected performance profile

- Net Sharpe: **0.3–0.5** standalone; its contribution is portfolio-level — negative correlation to trend/momentum sleeves raises *book* Sharpe more than its standalone number suggests.
- Skew: value-like — slow multi-year droughts, not crashes; drawdowns measured in years (the 2010s).
- Turnover: minimal; costs negligible (liquid index instruments); the most patient strategy in the corpus.

## 6. Failure modes & risks

- **Secular-regime risk:** a decade where the expensive keeps winning (2010s US tech/dollar) — value across assets is one correlated macro bet in such regimes despite class diversification.
- Anchor validity: CAPE comparability across accounting regimes; PPP for structurally-changing economies (terms-of-trade shifts); real-yield measures during inflation-expectation instability — anchors need maintenance and humility.
- Cheapness-for-a-reason: some markets are structurally discounted (governance, sanctions risk) — z-scores vs own history partially handle; country risk caps advisable.
- Fast reversals hurt the *momentum* partner, not value — but blended books must attribute correctly to avoid mis-learning.

## 7. Backtesting guidance

- Valuation anchors point-in-time (CAPE from as-known earnings, REER from published vintages); trailing-window z-scores strictly lagged.
- Instruments: futures where they exist (excess returns, roll-adjusted per corpus standards), ETFs elsewhere (costs/financing modeled).
- Long samples matter more than granularity: 30y+ monthly beats 10y daily for this signal class; assemble accordingly.
- Reports: per-class sleeve results, cross-sleeve correlation matrix, the value-vs-momentum correlation (should be negative — validation), blended 50/50 with momentum vs either alone, and drought-length statistics (max years underwater — set expectations honestly).
- Include the 2010s in full and report it straight: the pitch for this strategy survives *because* the drought is disclosed, not hidden.

## 8. Recommendations for use

- **Backtest priority: medium** — simple to build on the futures infrastructure (docs 02-02/03-01), and it completes the trend/carry/value triad that defines a modern systematic macro book.
- Deploy blended with cross-asset momentum (50/50) inside the futures book; standalone only if deliberately offsetting a trend-heavy allocation.
- Sizing rule as equity value: a size you hold through five bad years.
