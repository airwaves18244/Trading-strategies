# Futures Calendar-Spread / Term-Structure Relative Value

## 1. Classification

- **Category:** Arbitrage / relative value (curve RV)
- **Asset classes:** Commodity futures (energy, ags, metals), rates futures, VIX futures (see volatility docs), crypto futures curves
- **Style:** Market-neutral (outright-price-hedged) curve positioning
- **Horizon:** Days–months
- **Capacity:** Medium
- **Complexity:** Medium–high (requires per-market fundamentals awareness); **Data burden:** full futures chains (all expiries), daily settlements; storage/inventory data helpful

## 2. Economic rationale

A futures curve embeds storage economics and hedging pressure at each tenor. Calendar spreads (long one expiry, short another in the same market) isolate **relative tenor pricing** while cancelling outright price risk. Edges come from three distinct sources:

1. **Storage-arbitrage bounds (commodities):** contango is capped near full carry (storage + financing) — beyond it, cash-and-carry arbitrage kicks in. Spreads near full carry have asymmetric payoff: limited further widening, open-ended tightening if inventories draw. Backwardation has no such cap (scarcity can explode — the trade respects this asymmetry).
2. **Hedging-pressure segmentation:** producers hedge at specific tenors (e.g., 12-24m oil), consumers/index flows concentrate at the front → predictable relative cheapness/richness at flow-heavy tenors [T5, S3].
3. **Seasonal spread patterns with physical cause:** e.g., natural-gas winter/summer spreads driven by storage cycles; grain old-crop/new-crop spreads driven by harvest.

Counterparty: hedgers paying for tenor-specific insurance and index flows rolling mechanically. Compensation: warehousing curve risk and occasionally being run over by physical squeezes.

## 3. Signal & rules specification

Systematic baseline (per market, e.g., CL, NG, C, S, HG):

- **Spread series:** construct continuous calendar-spread series `sp = F_near − F_far` (specific tenor pairs, e.g., 1st–3rd, 2nd–6th), roll-adjusted.
- **Signal 1 — carry-bounded mean reversion (contango side only):** compute spread as % of estimated full carry (financing from rates + storage estimates per commodity). When spread ≥ ~85–95% of full carry, position for tightening (long near / short far is the *wrong* way here — you want long far/short near? No: at full contango, buy near-dated cheapness ⇒ **long near, short far** profits when contango tightens). Exit at 50% of full carry or on time stop (1–3 months). **Never mechanically short backwardation** (unbounded risk).
- **Signal 2 — spread momentum/inventory proxy:** 1–3 month change in the front spread is a robust inventory-direction proxy; trade spread continuation (tightening spreads → long near/short far). Holding 2–8 weeks.
- **Signal 3 — seasonal spreads:** predefined calendar entries with physical logic (e.g., long winter/short summer NG spread entered in shoulder season), tested per market; only trade seasonals with a storage/harvest story.
- **Sizing:** risk-based on spread volatility (spreads are lower-vol than outrights but jump; use 3–5x the daily σ as the stress unit). Per-spread risk ≤ 0.5% NAV. Diversify across ≥ 6–10 markets; signals are lowly correlated across markets.
- Margin efficiency: exchanges grant large spread-margin offsets — leverage discipline still required because spread margins understate squeeze risk.

## 4. Evidence & key research

- Gorton, Hayashi & Rouwenhorst (2013) [C5]: inventories drive the shape of the curve and risk premia — the fundamental anchor for signals 1–2.
- Mou (2011) [S3]: index-roll congestion made front-tenor spreads systematically cheap ahead of the GSCI roll window — 2000s version earned double-digit annual returns; substantially decayed (see doc `09-flows-seasonality/02`).
- Erb & Harvey (2006) [C6]: roll yield differentials across tenors as a persistent return source.
- Practitioner evidence: curve RV is a staple of commodity hedge funds; public track records (e.g., specialist commodity RV funds) show Sharpe ~0.8–1.5 with occasional squeeze losses.
- **Decay status: moderate.** Flow-based tenor effects decayed with index-flow sophistication; storage-bound and seasonal-physical edges persist because they require market-specific work and warehousing risk.

## 5. Expected performance profile

- Net Sharpe: **0.5–1.0** for a diversified multi-market spread book.
- Skew: negative on the short-backwardation side (avoided by construction), positive optionality when long near-dated scarcity; book-level roughly symmetric if rules above are followed.
- Turnover: moderate. Cost sensitivity: medium — spreads trade as native exchange instruments with tight quotes in liquid markets; far-tenor legs can be thin.

## 6. Failure modes & risks

- **Physical squeezes:** the catastrophic case is short the near leg into a delivery squeeze (WTI April 2020 going to −$37 was a front-contract storage event: anyone short the front spread the wrong way was destroyed). Position limits near expiry, exit before delivery/notice periods — mandatory rule.
- Storage-cost regime changes (2020: storage effectively "full", full-carry bound moved) — the bound is estimated, not observed.
- Cross-market contagion in commodity liquidations (2022 nickel, 2008): spread margins get raised, forcing exits at the wides.
- Model risk: a "cheap tenor" may reflect real physical information you don't have (pipeline outage, crop report leak) — mean-reversion entries should avoid days around scheduled physical data (EIA, WASDE) or at least expect losses there.

## 7. Backtesting guidance

- **Build spreads from individual contract series**, not from back-adjusted continuous outrights (back-adjustment destroys curve information). You need the full chain with actual expiry dates.
- Roll handling: define spread tenors by time-to-expiry buckets; roll on fixed days-before-expiry (test 5–15); never hold through first-notice for physically delivered contracts.
- Use settlement prices (they're the margining reality); model per-leg costs at 1–2 ticks + exchange fees; spread instruments where they exist.
- Full-carry estimation needs a financing rate series and storage-cost assumptions per commodity — document them; sensitivity-test ±50% on storage cost.
- Include 2020 (oil), 2021–22 (gas/power) in the sample — any spread backtest excluding these is decorative.
- Data: 15y+ full futures chains (CME/ICE settlements), ideally EIA/USDA inventory series for validation.

## 8. Recommendations for use

- **Backtest priority: medium.** High-quality diversifier (curve P&L ≈ orthogonal to outright trend/carry books), but data-engineering-heavy and per-market knowledge matters.
- Start with 2–3 markets you can learn deeply (e.g., CL, NG, corn) rather than a shallow 20-market sweep; seasonal-physical spreads in NG and grains are the most self-contained first project.
- Combine with the commodity-carry doc (`05-carry/02`) — same data infrastructure, complementary signals (carry = level of curve slope; this doc = relative tenor mispricing and change).
