# Breakout / Channel Trend Following (Donchian-Style)

## 1. Classification

- **Category:** Trend following (entry-timing variant)
- **Asset classes:** Futures multi-asset; crypto (works well — young, retail-heavy markets); FX
- **Style:** Directional, stop-managed, diversified
- **Horizon:** Breakout lookbacks 20–200 days; holds weeks–months
- **Capacity:** High
- **Complexity:** Low; **Data burden:** daily OHLC futures/crypto series

## 2. Economic rationale

Enter long when price exceeds its highest level of the past N days (short below the N-day low); exit on the opposite M-day channel or a volatility stop. Why this is *not* an indicator-only strategy: the N-day extreme is an **anchor and option-barrier level** — the same anchoring evidence as the 52-week-high effect [M5] says market participants under-bid through reference extremes, so a *breach* of the extreme carries genuine information about demand/supply imbalance (someone is willing to pay through the level everyone watches). Breakouts also coincide with hedger capitulation and stop-cascades that *extend* moves (reflexive flow). Economically it is the same trend premium as doc 01 harvested with a different estimator: MA-crossover systems and channel systems produce highly correlated returns [T4] — the channel version trades less often, enters later (demands more confirmation), and has a natural built-in exit discipline.

Practitioner provenance: Donchian (1960s), Turtle rules (1980s — Dennis/Eckhardt), long CTA lineage; the survival of channel systems for 60 years across regimes is itself evidence of robustness (with the caveat that the *published* Turtle-era Sharpe reflected a golden age of commodity trends).

## 3. Signal & rules specification

Turtle-style modernized baseline:

- **Universe:** 20–50 liquid futures (or top-20 crypto for the crypto variant).
- **Entry:** stop-order long at breach of N-day high; short at N-day low. Two-speed ensemble: N ∈ {20, 55} classic (test range 20–100). Optional filter: skip signal if the *previous* same-direction breakout won (classic S1 filter) — modest evidence, test rather than assume.
- **Initial stop:** 2·ATR(20) from entry (range 1.5–3).
- **Trailing exit:** opposite M-day channel with M ≈ N/2 (10 for 20, 20 for 55), or ATR trailing stop — whichever is nearer.
- **Position size:** risk-unit based: `contracts = (0.5–1% NAV) / (2·ATR · point_value)` — identical in spirit to vol targeting; per-market and per-sector risk caps; portfolio vol target 10–15%.
- **Pyramiding (optional, classic):** add ½ unit each ½·ATR favorable move up to 4 units — increases skew and drawdowns; test both.
- **Rebalance/monitoring:** daily; stops live in-market.

## 4. Evidence & key research

- Equivalence result [T4]: channel/breakout, MA-crossover, and TS-momentum signals are one family — expect correlation ≈ 0.7–0.9 to doc 01 returns; evidence base therefore inherits [T1][T2][T3].
- Anchoring evidence [M5] provides the behavioral basis for level-breach information content.
- Practitioner record: documented Turtle-program results (1984–88, very high returns — small sample, golden regime); long-running channel CTAs (e.g., Mulvaney, Dunn — public track records) show the strategy alive with Sharpe ~0.4–0.6 and extreme positive skew (occasional +50% years, long shallow drawdowns).
- **Decay status:** as trend generally [T6][T7]; short-lookback breakouts (N ≤ 20) decayed most (noise arbitraged); slower breakouts (55–100d) track the broad trend premium.

## 5. Expected performance profile

- Net Sharpe: **0.3–0.6** diversified; do not expect it to beat the doc-01 ensemble — expect *similar with fewer trades and lumpier wins*.
- Skew: strongly positive (hard stops truncate left tail; open-ended rides); win rate low (30–45%) with payoff ratio > 2 — psychologically hard, statistically fine.
- Turnover: low–moderate. Cost note: stop-entries pay taker spread + slippage at exactly the moments everyone's stops trigger — model breakout slippage above average (see §7).
- Crypto variant: historically strong (2017, 2020–21, 2023–24 cycles are breakout-friendly); vol scaling essential.

## 6. Failure modes & risks

- **False-breakout chop:** rangebound markets repeatedly trigger entries at range edges then stop out — the dominant loss mode; slower N and the ensemble mitigate.
- Slippage clustering: breakout levels are visible to everyone; entries fill worse than mid (institutional stop-hunting around obvious levels is real but is a cost, not a refutation — the move after genuine breakouts dwarfs it).
- Gap risk through stops (limit-down moves, crypto weekends): stops don't bound losses to plan; size for gap scenarios.
- Same regime risks as all trend (2012–2017-type droughts).

## 7. Backtesting guidance

- Simulate stop-order mechanics honestly: entry at breakout level + slippage (model ≥ 0.5–1·ATR/10 or use next-bar open if breach on close); never fill at the breach print itself with zero slippage.
- OHLC data quality matters (channel highs/lows from bad ticks fabricate breakouts — clean or use close-only channels as robustness check).
- Test N/M over ranges and report the *surface*, not the best cell — the claim is robustness across parameters; a spiky surface = curve-fit.
- Run head-to-head vs doc-01 MA-ensemble on identical universe/costs; report correlation and incremental Sharpe of combining (expected: small but positive from timing diversification).
- Include pyramiding on/off; include the gap-risk stress (limit moves).
- Data: 20y+ futures OHLC; crypto since 2017.

## 8. Recommendations for use

- **Backtest priority: medium.** Value is (a) an independent estimator check on the trend premium, (b) the best construction for **crypto trend** (where stop-discipline against 80% drawdowns is non-negotiable), (c) a low-trade-count implementation for capital that can't support daily-managed systems.
- In a full futures book, fold it into the doc-01 ensemble as one more signal speed/type rather than a separate allocation.
- If trading crypto trend: this construction, halved risk units, and no pyramiding is the recommended spec.
