# VIX Term-Structure Signal Trading (Two-Sided)

## 1. Classification

- **Category:** Volatility (term-structure state trading)
- **Asset classes:** VIX futures (VSTOXX secondary); equity index futures as companion leg
- **Style:** Time-series, two-sided (short-vol *and* long-vol states)
- **Horizon:** Days–weeks per position
- **Capacity:** Medium
- **Complexity:** Medium; **Data burden:** VIX futures curve + VIX + realized vol (daily; no options chains)

## 2. Economic rationale

Distinct from always-harvesting carry (doc 05-04): here the **shape and dynamics of the vol term structure are the signal for regime**, traded both directions. The logic: the VIX curve aggregates hedging demand across horizons. **Steep contango** = calm regime with overpriced near-term insurance → short-vol states pay. **Inversion (backwardation)** = panic regime; crucially, panic states exhibit *persistence* — vol spikes decay over weeks (vol clustering), and the inverted curve systematically **underprices how slowly vol mean-reverts**, so long positions in deferred futures during early backwardation, or staying long vol while inversion persists, have positive expectancy [V5-adjacent evidence; vol-clustering literature]. Additional documented structure: the curve's *slope changes* lead equity returns (vol regime shifts front-run equity drawdowns), enabling a companion equity de-risking signal. Counterparties: mechanical ETP rebalancing flows (predictable, large [V4]) and panicking/complacent hedgers on each side.

## 3. Signal & rules specification

- **State variables (daily):** basis `b1 = VX1/VIX − 1`, slope `b2 = VX2/VX1 − 1`, and their 5-day changes; realized-vs-implied gap (VIX − RV20) as confirmation.
- **Regime rules:**
  - **Calm-carry state:** b1, b2 > +2–4% and stable → short front/mid vol (this overlaps doc 05-04 — run as one book to avoid duplication).
  - **Transition state:** contango flattening rapidly (Δb1 < −2–3% over ≤ 5 days) while VIX < long-run mean → *flat vol, reduce equity beta* (the early-warning use).
  - **Panic state:** b1 < −2% (inversion) → long VX1/VX2 (riding persistence) **or** stand aside if entered late (inversion age > ~10 sessions historically marks decay onset); exit longs as curve re-normalizes (b1 > 0).
  - **Normalization trade:** after inversion peaks, short front vol into re-steepening — historically the highest-Sharpe state but requires surviving to trade it.
- **Sizing:** per-state vol-scaled; long-vol positions sized larger than shorts per unit margin (positive-skew side); portfolio share ≤ 10% risk.
- Parameters above are ranges to test, not constants; the *states* are the spec.

## 4. Evidence & key research

- Simon & Campasano [V5]: basis predicts VIX futures returns both directions — the core evidence.
- Vol clustering/persistence (Engle onward; HAR literature): spikes decay over weeks — the panic-state persistence basis.
- ETP flow mechanics [V4]: end-of-day rebalancing of levered/inverse VIX ETPs creates predictable flows in stress — a structural counterparty.
- Live: two-sided versions navigated 2018/2020 far better than short-only (long legs paid); 2022's slow-burn bear was the hard case — vol stayed *mid* (no fat contango, no true panic) and chopped state models.
- **Decay status: moderate;** the short side shares 05-04's compression; the long-side persistence edge is structurally harder to crowd (requires buying into fear).

## 5. Expected performance profile

- Net Sharpe: **0.4–0.7** full-cycle for the state machine; lower than pure carry in calm decades, much better through vol events.
- Skew: roughly **neutral to positive** — the design goal; the long-states are the corpus's only native positive-skew vol allocation.
- Turnover: moderate-high around state flips; futures costs low.

## 6. Failure modes & risks

- **Mid-vol chop (2022-type):** neither regime cleanly triggers; whipsaw across thresholds — hysteresis in state definitions (different entry/exit thresholds) is the standard fix.
- Late-inversion longs: buying vol after the spike peak bleeds carry brutally — the inversion-age rule matters.
- Short-side risks identical to 05-04 (gap inversions) when in calm-carry state.
- Regime model overfit: 4 states + thresholds on ~6 historical spike episodes = overfitting risk; keep thresholds coarse and validate on VSTOXX as the out-of-sample market.

## 7. Backtesting guidance

- Same data/method base as 05-04 (CBOE settlements 2004+, constant-maturity construction, gap-realistic fills).
- Backtest as an explicit **state machine** with logged state history; report per-state P&L, state-flip counts, and whipsaw cost — the strategy is only as good as its transition behavior.
- Include: 2008, 2010 flash crash, 2011, Aug-2015, Feb-2018, Mar-2020, 2022 (the failure case to study), Aug-2024.
- Cross-validate the state definitions on VSTOXX futures (independent market, same structure).
- Compare against 05-04 alone: the claim to validate is *similar return, radically better crash profile* — if the two-sided version doesn't show that, run carry-only.

## 8. Recommendations for use

- **Backtest priority: medium-high** (immediately after 05-04 — shared infrastructure, and the comparison IS the research).
- Deploy as the *risk-managed evolution* of vol carry: one book implementing the calm-state carry + panic-state long + normalization trades, replacing a standalone short-vol sleeve.
- The transition-state early-warning signal doubles as a portfolio-level de-risking input for equity sleeves — value beyond its own P&L.
