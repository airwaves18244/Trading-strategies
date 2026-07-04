# Commodity Carry (Backwardation / Roll Yield)

## 1. Classification

- **Category:** Carry (commodities)
- **Asset classes:** Commodity futures (20–30 markets)
- **Style:** Cross-sectional long-short (and TS tilt)
- **Horizon:** Monthly rebalance
- **Capacity:** Medium–high
- **Complexity:** Medium (seasonality handling); **Data burden:** full futures chains per commodity

## 2. Economic rationale

The slope of a commodity's futures curve forecasts its excess return: **backwardated** markets (front above deferred) outperform **contangoed** ones. Two reinforcing theories with empirical support:

1. **Theory of storage / inventories [C5]:** backwardation signals scarcity (low inventories ⇒ convenience yield high). Scarcity states carry positive expected returns because inventory can't be conjured — the risk of stock-out is priced.
2. **Hedging pressure (Keynes' normal backwardation, modernized [T5]):** producers hedge future output by selling deferred contracts, depressing them below expected spot; the long earning the roll-up is being paid an insurance premium for absorbing producer price risk. In contango markets, consumer/index hedging pressure flips the sign.

Counterparty: commercial hedgers (documented via CFTC positioning) and passive long-only index flows mechanically rolling in contango. The carry return realizes as **roll yield** — holding a backwardated contract that "rolls up" the curve toward spot.

## 3. Signal & rules specification

- **Universe:** the 20–30 market set from doc 02-07 (shared infrastructure).
- **Carry signal:** annualized slope `c = ln(F_near/F_far) / Δτ` between (a) front and second contract, or better (b) **same-month-next-year** pair for seasonal commodities (gas, ags) — raw front-slope in seasonal markets measures the season, not carry. Deseasonalized carry is the professional convention; non-seasonal metals/energy can use adjacent tenors.
- **Portfolio:** rank cross-sectionally; long top ~⅓ (most backwardated), short bottom ~⅓; inverse-vol weights; sector risk caps (≤ 40%).
- **TS variant:** long markets with c > 0, short c < 0, per-market — test alongside CS.
- **Rebalance:** monthly; roll away from index-roll congestion windows.
- **Composite recommendation (from doc 02-07):** combine carry z with 12-month momentum z ~50/50 — both proxy inventory states from different angles; the composite is the literature-standard commodity strategy.
- Vol-target book 8–12%; stress-vol sizing for squeeze-prone markets.

## 4. Evidence & key research

- Gorton & Rouwenhorst (2006) + GHR (2013) [C5]: inventory/backwardation → returns mechanism; portfolios sorted on basis earn large spreads (high-basis minus low-basis ~8–10%/yr in-sample).
- Erb & Harvey (2006) [C6]: roll yield explains the cross-section of long-run commodity returns; the famous "the average commodity return ≈ 0, the strategy return ≠ 0" point.
- Koijen et al. [C1]: commodity carry Sharpe among the strongest of the 9 classes in their sample.
- Kang, Rouwenhorst & Tang (2020) [T5]: positioning data confirms hedging-pressure transfer as the payer.
- Post-publication: 2010s weaker (broad contango decade, financialization), 2020–2022 exceptional (inflation/scarcity). Long-run premium credible with the standard haircut.
- **Decay status: partial;** the physical mechanism (inventories, hedging demand) regenerates and cannot be fully arbitraged without warehousing physical risk.

## 5. Expected performance profile

- Net Sharpe: **0.4–0.7** diversified CS carry (higher for the carry+momentum composite); low correlation to equities/bonds and to FX carry — carry premia across classes are surprisingly independent [C1].
- Skew: negative-ish (short squeezes on the short leg; scarcity spikes helping longs partially offset — milder than FX carry's skew).
- Turnover: low–moderate; costs manageable in liquid markets, wider in ags/softs.

## 6. Failure modes & risks

- **Seasonality contamination:** the #1 spec error (see §3) — naive front-slope signals in NG/ags trade the calendar, not carry.
- Short-leg squeezes: shorting contangoed markets means shorting high-inventory commodities — usually safe, but supply shocks flip states fast (2021–22 gas: contango → violent backwardation).
- Index-flow interaction near rolls; margin spikes in stressed markets.
- Broad-commodity bear/contango regimes (2013–2019): the long leg starves.

## 7. Backtesting guidance

- Full-chain data mandatory (as docs 01-06/02-07); construct carry from actual contract pairs with correct day counts; deseasonalize per §3 and *show both versions* — the gap between naive and deseasonalized results is a pipeline validation.
- Excess returns from roll-adjusted series; roll-window costs explicit.
- Mechanism validation: carry-sorted portfolio returns should correlate with inventory measures (EIA/USDA/LME) and CFTC commercial positioning — run it; it's the anti-data-mining check.
- Joint test with commodity momentum (doc 02-07 §7): incremental Sharpe of each given the other; budget as one inventory-state bet accordingly.
- Sample: 20y+ including 2008, 2014–15, 2020–22.

## 8. Recommendations for use

- **Backtest priority: high** (as the carry half of the commodity composite; shared data infra with docs 01-06, 02-07 makes marginal cost low).
- Deploy as carry+momentum composite within the futures risk-premia book (doc 03-03 integration); sector caps and deseasonalized signals are non-negotiable spec items.
- Best-grounded carry premium in the corpus (physical mechanism + positioning data) — deserves its capital.
