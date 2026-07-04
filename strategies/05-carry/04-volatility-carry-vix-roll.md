# Volatility Carry (VIX Futures Roll-Down)

## 1. Classification

- **Category:** Carry (volatility) — cross-listed with category 06
- **Asset classes:** VIX futures (and VSTOXX; ETPs as retail wrappers)
- **Style:** Time-series short-carry with state switches
- **Horizon:** Daily monitoring; positions held days–weeks
- **Capacity:** Medium (VIX futures liquidity concentrated at front)
- **Complexity:** Medium; **Data burden:** VIX futures full curve daily + VIX/realized vol; no options chains needed — the accessible vol strategy

## 2. Economic rationale

The VIX futures curve sits in **contango ~75–85% of days**: deferred futures price vol above spot VIX because investors persistently overpay for future volatility exposure — the same variance risk premium (doc 06-01) expressed in listed futures. A short front-month VIX future earns the roll-down as the contract converges to (usually lower) spot. Who pays: hedgers buying vol protection (portfolio insurance demand is price-insensitive), long-vol ETP flows, and structured-product vega demand. The seller is short crash insurance: in vol spikes the curve inverts and shorts lose multiples of typical monthly gains in days (Feb-2018: front VIX future +96% in a day; XIV terminated [V4]). The signal content: **the basis itself predicts the P&L** — steep contango = fat expected roll + calm-state probability; backwardation = the insurance is on fire, stand aside or flip long.

## 3. Signal & rules specification

Simon-Campasano-style baseline [V5]:

- **Instruments:** front and second VIX futures (VX1, VX2); constant-maturity blend optional.
- **Basis signal:** `b = (VX1 − VIX)/VIX` (or VX2−VX1 slope). Daily.
- **Rules:**
  - Short VX1 (or short constant-maturity blend) when `b > +θ_s` (θ_s ≈ 2–5%; steep contango);
  - Flat when |b| ≤ θ (the mush zone);
  - Optional long VX1 when `b < −θ_l` (backwardation ≈ crisis; long-vol leg funded by the short leg's history — test separately; evidence weaker but it's the tail hedge).
- **Hard risk rules (these are the strategy):**
  - Position size such that a **VIX +20-point overnight** move loses ≤ 3–5% NAV (sizes positions at a fraction of "vol-based" sizing);
  - Stop/de-risk on curve flattening: exit shorts when b crosses below +1% *before* inversion, don't wait for the fire;
  - No adding to losing shorts, ever.
- **Sizing:** vol carry ≤ 5–10% of portfolio risk budget; it's a return enhancer, not a core.
- **Rebalance:** daily evaluation; roll shorts before final-week convergence chop.

## 4. Evidence & key research

- Simon & Campasano [V5]: basis-conditional short strategy profitable 2007–2011+ sample, capturing the roll while sidestepping some inversions.
- Volmageddon post-mortem [V4]: the flow-feedback anatomy (inverse ETPs' contractual rebalancing amplified the spike) — the definitive failure-mode case study; short-vol ETP AUM never fully returned [V4].
- VRP magnitude [V1][V6]: ~3–4 vol points average implied−realized on SPX, positive ~85% of months — the underlying premium source.
- Live: post-2018 the front-curve carry compressed (market learned; dealers charge more for the tail), but contango-conditional strategies remained positive through 2019, got destroyed-or-saved in Feb/Mar-2020 depending entirely on the de-risk rule speed, and earned steadily 2021–25 outside spike weeks.
- **Decay status: moderate compression + fully intact tail risk.** The premium persists because the loss states are genuinely terrible.

## 5. Expected performance profile

- Net Sharpe **0.5–0.9** for basis-conditional versions across full cycles *if* the risk rules hold; raw always-short: higher Sharpe until the day it's −40%.
- Skew: **extremely negative** — the defining feature; expect years of 10–20% annual carry then a −15–30% week if rules slip.
- Turnover: moderate; costs low (liquid futures, ~1 tick spreads front months).

## 6. Failure modes & risks

- **Gap inversions:** overnight/weekend vol spikes skip the de-risk trigger (Feb-2018 was largely one session) — the overnight-loss sizing rule is the only real defense.
- Feedback crowding: short-vol positioning itself amplifies spikes [V4]; monitor ETP AUM/short interest as regime input.
- Basis measurement near expiry (convergence noise) and roll timing.
- Psychological: the strategy trains complacency — years of wins before the test; mechanical rules or don't run it.

## 7. Backtesting guidance

- Data: CBOE publishes full VIX futures settlement history (2004+) — build the curve, constant-maturity series, and basis daily. Include Feb-2018, Aug-2015, Oct-2008, Feb–Mar-2020, Aug-2024 — **the backtest is graded on these weeks**.
- Simulate the de-risk rule at realistic speed: signals at close → exit next open at the *gapped* price; no intraday-stop fantasy fills through a spike.
- Report: P&L attribution (roll capture vs spot-vol change), the worst-10-days table, results with the long-backwardation leg on/off, and sensitivity to θ thresholds.
- Benchmark vs the short-VXX-and-hold baseline (must beat it on drawdown-adjusted terms by construction, or the conditioning is worthless).
- 20y history covers 3 full vol cycles — sufficient but treat N(spikes) ≈ 6 as the real sample size.

## 8. Recommendations for use

- **Backtest priority: high within the vol family** — it's the vol risk premium harvestable with daily futures data only (no options infrastructure), making it the natural first vol strategy.
- Deploy small, rules-locked, with the overnight-gap sizing constraint as the binding limit; pair with trend (which tends to be long defensively when vol carry burns) and never stack with other short-crash sleeves (merger arb, stat-arb, FX carry) without joint tail budgeting.
