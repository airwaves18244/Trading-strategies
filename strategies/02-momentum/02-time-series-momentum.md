# Time-Series (Absolute) Momentum — Multi-Asset

## 1. Classification

- **Category:** Momentum (time-series); overlaps trend following (see `03-trend-following/01` for the full trend treatment)
- **Asset classes:** Futures across equities, rates, FX, commodities; ETFs; crypto
- **Style:** Directional per-asset, diversified across many markets
- **Horizon:** Signal 1–12 months; monthly/weekly rebalance
- **Capacity:** Very high
- **Complexity:** Low; **Data burden:** daily futures/ETF total-return series, roll-adjusted

## 2. Economic rationale

Each asset's *own* past return predicts its next 1–12 month return. Distinct from cross-sectional momentum: no ranking against peers — every market can be long or short simultaneously. Mechanisms: (a) **slow information diffusion & anchoring** (same behavioral engine as CS momentum), (b) **non-price-sensitive flows** — central banks, corporate hedgers, and rebalancing programs push prices gradually, (c) **risk transfer:** trend followers effectively buy insurance underwriting from hedgers who sell exposure into declines and buy into rallies (Kang-Rouwenhorst-Tang [T5]). Counterparty: hedgers paying for immediacy and investors who rebalance against trends. TSMOM's crisis payoff (long bonds/short equities in drawn-out bear markets) is a genuine hedging property, not decoration.

## 3. Signal & rules specification

- **Universe:** 30–60 liquid futures markets across the four asset classes (diversification across markets is where the Sharpe comes from — 10 markets is not enough).
- **Signal (MOP baseline [M3]):** sign of past 12-month excess return: `s_i = sign(r_{i,t−12→t})`. Robust extensions: average of sign signals at 1, 3, 6, 12 months (reduces timing luck); or t-statistic-scaled signal `s = clamp(r/σ_annualized, −1, 1)` for continuous sizing.
- **Position sizing (essential, not optional):** inverse-volatility: `w_i = s_i · (σ_target / σ_i)` with σ_i = ex-ante vol (e.g., 60-day EWMA annualized), σ_target ≈ 10–40%/n per market such that **portfolio** vol targets 10–15% annualized. The vol-scaling is half the strategy: it equalizes risk across bonds vs commodities and de-levers in vol spikes.
- **Rebalance:** monthly baseline (test weekly — improves crisis responsiveness at cost of turnover); roll futures per market conventions.
- Portfolio cap: cap aggregate exposure per asset class (e.g., ≤ 40% of risk) to prevent rate-market domination.

## 4. Evidence & key research

- Moskowitz, Ooi & Pedersen (2012) [M3]: 58 futures markets 1985–2009; 12-month TSMOM positive in every market; diversified portfolio gross Sharpe ~1.0+; profits partially explained by hedging-pressure positioning.
- Hurst, Ooi & Pedersen (2017) [T1]: extended to 1880 — positive in every decade, through wars/depressions/regimes; best years cluster in sustained crises ("crisis alpha": 1930s, 2008, 2022).
- Baltas & Kosowski [T2]: TSMOM replicates CTA index returns (R² high, alpha ≈ 0 after TSMOM) → the strategy *is* the managed-futures industry; no evidence of capacity constraints at studied AUM.
- Live decay check [T6, T7]: SG Trend +20.1% in 2022 (best since 2000) but weak 2015–2019 and 2023–25 stretches; post-crisis periods show ~halved returns for ~4 years [T7]. Long-run premium intact but Sharpe of simple versions ~0.5–0.7 net in the modern era vs ~1.0 in-sample.
- **Decay status: modest but real;** the 2022 outcome confirms the crisis-convexity property survives.

## 5. Expected performance profile

- Net Sharpe (30+ markets, vol-targeted): **0.5–0.8**; single-market Sharpe ~0.1–0.2 (the strategy is a diversification machine).
- Skew: **positive at horizon of months** (cuts losers, rides winners) — the rare strategy with crisis-convex payoff; expect death-by-a-thousand-cuts in choppy rangebound years (2015–2019).
- Turnover: moderate (vol scaling adds some). Cost sensitivity: low–medium in liquid futures (~1–3bp per trade); meaningful only in the weekly/fast variants.

## 6. Failure modes & risks

- **Whipsaw regimes:** rangebound markets with sharp reversals (2015–2019) produce multi-year flat-to-negative stretches — behavioral risk of abandoning it right before it pays (most investors did, before 2022).
- Sharp V-reversals faster than the signal horizon (March→April 2020: trend got short equities at the bottom).
- Correlation spikes across markets in macro regimes (2022 helped; an inflation-crash regime where bonds and equities trend *against* the book simultaneously would hurt).
- Crowding: large CTA industry; evidence of capacity constraint weak [T2], but entry/exit clustering around common signal levels causes local slippage events.

## 7. Backtesting guidance

- **Roll-adjusted continuous futures** (back-adjusted for P&L; unadjusted for levels): the difference between price return and total futures return is carry — mixing them up is the classic error that overstates commodity TSMOM.
- Use excess returns (futures are self-financing); if using ETFs, subtract financing properly.
- Ex-ante vol only (no look-ahead in σ); trade at next close/open after signal; include per-market costs and realistic roll costs.
- Validate against published results: your 1985–2009 12-mo TSMOM should approximate MOP's; then extend to present and report the post-2009 sample separately (the honest out-of-sample).
- Report per asset class and correlation to 60/40 in the worst 10 equity quarters (the crisis-alpha claim is testable and should reproduce).
- Minimum data: 20y+, ≥ 30 markets; 40y across asset classes ideal.

## 8. Recommendations for use

- **Backtest priority: highest in corpus.** Best-documented, most robust, highest-capacity strategy here; also the reference infrastructure (roll handling, vol targeting) for carry, curve, and trend docs.
- Core allocation candidate, sized as a permanent sleeve (10–25% of risk) precisely *because* of its positive skew and crisis behavior — do not performance-chase in and out.
- Combine multiple lookbacks + vol targeting; resist over-optimizing lookbacks (robustness across 3–12m is the point).
