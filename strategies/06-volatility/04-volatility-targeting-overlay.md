# Volatility Targeting / Managed-Volatility Overlay

## 1. Classification

- **Category:** Volatility (portfolio-construction overlay — a strategy *improver*, cross-cutting)
- **Asset classes:** Any (documented on equities, factor portfolios, futures books, crypto)
- **Style:** Exposure scaling rule on an underlying strategy
- **Horizon:** Daily–weekly adjustment
- **Capacity:** Unlimited (it's a scaler)
- **Complexity:** Low; **Data burden:** returns of the underlying + a vol estimator — trivial

## 2. Economic rationale

Scale exposure inversely to recent realized volatility: `w_t = σ_target / σ̂_t` (capped). Two empirical facts make this add value rather than being cosmetic:

1. **Volatility clusters and is forecastable** (the most robust stylized fact in finance): high vol today → high vol next weeks. Variance is predictable even though returns barely are.
2. **The risk-return trade-off is flat-to-inverted at short horizons:** high-vol periods do *not* offer proportionally higher returns (for equities, average returns after vol spikes are no higher, and vol-scaled Sharpe improves — Moreira & Muir [V7]); for negative-skew strategies (momentum, carry), crashes concentrate in high-vol states, so de-scaling then cuts tails specifically (Barroso-Santa-Clara [M10], Daniel-Moskowitz [M9]).

So the overlay sells exposure precisely when variance is high but expected return isn't — improving Sharpe and, for crash-prone strategies, skew. Who's on the other side: investors with constant-notional habits and those forced to *buy* risk in calm (leverage-constrained reaching) and hold through storms. Included as a "strategy" because its documented effect sizes rival many alphas, at near-zero cost.

## 3. Signal & rules specification

- **Vol estimator:** EWMA of daily returns, λ ≈ 0.94 (≈ 20d half-life) or simple 20–60d realized; HAR for refinement. Use the *underlying strategy's* return vol (not just market vol).
- **Rule:** `exposure_t = clamp(σ_target / σ̂_{t−1}, floor, cap)` with cap ≈ 1.5–2.0x, floor ≈ 0.3–0.5x; σ_target = the strategy's long-run vol or a chosen budget.
- **Rebalance:** daily calculation, trade on threshold breaches (±10–20% exposure change) to control turnover.
- **Application map (from the corpus):** equity market exposure [V7]; momentum sleeves [M9][M10] (largest documented improvement — crash mitigation); carry books; trend books already embed it (docs 02-02/03-01 — don't double-apply); panic-reversion (04-02) deliberately does the *opposite* (buys vol spikes) — never wrap this overlay around counter-cyclical liquidity-provision strategies without thinking.
- **Anti-pattern warning:** industry-wide vol targeting creates the very deleveraging cascades (Feb-2018, Mar-2020) that docs 04-02 and 05-04 discuss — being a *small* vol-targeter among giants is fine; know you're in that crowd.

## 4. Evidence & key research

- Moreira & Muir (2017) [V7]: vol-managed versions of market, value, momentum, profitability, FX carry portfolios raise Sharpe and utility for most; effect strongest for momentum.
- Barroso & Santa-Clara [M10]: momentum max DD −96% → −45%, Sharpe ~doubles.
- Daniel & Moskowitz [M9]: crash forecastability by vol/bear states.
- Critiques (balance): Cederburg et al. (2020) show out-of-sample utility gains are smaller and sensitive to costs/leverage limits for *the market* portfolio; consensus: robust for negative-skew factor strategies, mild for buy-and-hold indices.
- **Decay status: n/a in the usual sense** (not an anomaly but a variance-forecasting harvest); crowding manifests as the flow-cascade externality, not premium erosion.

## 5. Expected performance profile

- Expected improvement, not standalone return: **+0.1–0.3 Sharpe** and 30–50% max-DD reduction on crash-prone underlying strategies; ~neutral-to-mildly-positive on already-symmetric ones.
- Adds turnover: 20–60% annually of the underlying's notional (threshold rebalancing at the low end).
- Changes return shape: fewer extreme months both directions; slight lag cost in V-recoveries (de-levered at the bottom — the known fee).

## 6. Failure modes & risks

- **V-bottom lag:** scaled down after the crash, missing the rebound (2020-Q2) — the cost of the insurance; cap/floor bounds limit it.
- Vol-of-vol whipsaw: rapid vol regime flips cause buy-high/sell-low exposure churn; thresholds and EWMA smoothing mitigate.
- Estimator gaming in backtests: intraday-informed vol estimates with EOD execution = look-ahead; keep estimator strictly lagged.
- Systemic: the crowd effect above — treat sudden market-wide de-risking days as *your* strategy's crowding events.

## 7. Backtesting guidance

- Test as an A/B wrapper on each strategy already built: identical everything, overlay on/off; report Sharpe, max DD, skew, turnover delta, and cost-adjusted improvement.
- Strictly lagged σ̂ (t−1 close data for t exposure); execution next open/close.
- Sensitivity: estimator window/λ, cap/floor, threshold — improvements should be robust across reasonable settings (they are, in the literature; verify on your book).
- The momentum wrap [M10 replication] is the highest-value single test: it should reproduce the documented crash mitigation on your momentum sleeve or something's off.

## 8. Recommendations for use

- **Backtest priority: high (as infrastructure)** — build once as a reusable module early; it upgrades half the corpus.
- Default-on for: momentum (CS & residual), FX/vol carry, equity beta sleeves. Default-off for: trend/TSMOM (already embedded), panic-reversion and other deliberately counter-cyclical strategies.
- Portfolio level: a book-level vol target (8–12%) on top of sleeve-level targets is standard institutional practice and recommended here.
