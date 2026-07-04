---
title: "Non-HFT Trading Strategies — Research Report"
project: trading-strategies-research
flow: universal
effort: deep
date: 2026-07-04
status: final
---

# Non-HFT Trading Strategies — Research Report

## Executive summary

**Which non-HFT strategies justify a high-quality backtest?** Of the 43 strategies investigated (~28–30 economically independent approaches), the strongest candidates share one profile: **diversified, macro-consistent risk premia with an identifiable payer** — trend following / time-series momentum, cross-asset carry, commodity carry+momentum, the variance risk premium, and equity factor pairs (momentum+value+quality). These survive because they compensate real risk (crash, liquidity, inventory) or exploit durable constraints, not because they are secrets. A second tier of **structural-flow and information edges** (buybacks/insider signals, PEAD in inattentive pockets, ETF stress dislocations, panic mean-reversion, crypto funding arbitrage) remains viable but demands cost engineering and decay monitoring. A deliberate control group of **decayed anomalies** (index-addition front-running, pre-FOMC drift, naive overnight drift, Goldman-roll front-running) is documented with decay curves — both as a warning and as pipeline-validation material.

The central quantitative fact governing expectations: published equity anomalies lose **~26% of returns out-of-sample and ~58% post-publication** (McLean-Pontiff [X1]). Every performance range in this corpus is stated net of that haircut; no strategy is presented at in-sample magnitude. Realistic standalone net Sharpe for almost everything here is **0.3–0.8**; the portfolio-level prize comes from combining lowly-correlated sleeves (a trend+carry+factors book at Sharpe ~1 is achievable; any single strategy claiming that alone is suspect).

## Background & research question

Full question, scope, sub-questions (SQ1–SQ10), and success criteria: [research/00-brief.md](research/00-brief.md). Method: universal flow (Phase 0–5) from [airwaves18244/REASERCH-PLAN](https://github.com/airwaves18244/REASERCH-PLAN); sources logged and credibility-rated in [research/01-landscape.md](research/01-landscape.md); red-team pass in [research/04-critique.md](research/04-critique.md). Constraints honored: no HFT, no indicator-only strategies (every entry names its economic mechanism and counterparty), specs at backtest-ready detail with parameter ranges, no code.

## What was investigated

43 strategy documents across 10 categories. Each follows the same 8 sections: classification, economic rationale, signal & rules spec, evidence & decay status, expected performance, failure modes, backtesting guidance, recommendations.

## Master comparison

Edge types: **RP** = risk premium, **B** = behavioral, **SF** = structural/flow, **C** = constraint/friction. Sharpe = realistic standalone net range from the docs. Priority = backtest priority. ⚠ = flagged (data/infra-heavy or decayed core).

| # | Strategy | Edge | Horizon | Net Sharpe | Skew | Capacity | Cost sens. | Data burden | Decay | Priority |
|---|----------|------|---------|-----------|------|----------|-----------|-------------|-------|----------|
| 1 | [Pairs trading](strategies/01-arbitrage-relative-value/01-pairs-trading.md) | SF/C | days–2m | 0.3–0.7 | neg | low-med | decisive | med | heavy | med-high |
| 2 | [Stat-arb residual portfolios](strategies/01-arbitrage-relative-value/02-statistical-arbitrage-mean-reverting-portfolios.md) | SF/C | 1–20d | 0.5–1.0 | neg | med | extreme | med | substantial | high |
| 3 | [Cash-and-carry basis](strategies/01-arbitrage-relative-value/03-futures-cash-and-carry-basis.md) | C | wks–mo | episodic | mild neg | med-high | low-med | low | cyclical | med |
| 4 | [ETF–NAV arbitrage](strategies/01-arbitrage-relative-value/04-etf-nav-arbitrage.md) | SF | intraday–mo | 0.5–0.8 (B) / episodic (A) | mixed | low-med | med | med | intraday dead; stress alive | med |
| 5 | [Merger arbitrage](strategies/01-arbitrage-relative-value/05-merger-arbitrage.md) | RP | 1–12m | 0.6–1.0 | strong neg | med-high | med | high (deal DB) | modest | med |
| 6 | [Calendar-spread / curve RV](strategies/01-arbitrage-relative-value/06-futures-calendar-spread-term-structure-rv.md) | RP/SF | days–mo | 0.5–1.0 | ~sym | med | med | high (chains) | moderate | med |
| 7 | [Convertible arbitrage ⚠](strategies/01-arbitrage-relative-value/07-convertible-bond-arbitrage.md) | C/RP | mo–yrs | 0.7 cycle | neg | med | high | very high | cyclical | low |
| 8 | [CS equity momentum 12-1](strategies/02-momentum/01-cross-sectional-equity-momentum.md) | B | 3–12m | 0.3–0.6 (0.5–0.8 managed) | strong neg | high | med | med | partial | high |
| 9 | [Time-series momentum](strategies/02-momentum/02-time-series-momentum.md) | RP/B | 1–12m | 0.5–0.8 | pos | very high | low-med | med (futures) | modest | highest |
| 10 | [Residual momentum](strategies/02-momentum/03-residual-idiosyncratic-momentum.md) | B | 12-1 | 0.5–0.8 | mild neg | high | med | med | partial | high |
| 11 | [Industry & factor momentum](strategies/02-momentum/04-industry-and-factor-momentum.md) | B/SF | 1–12m | 0.3–0.7 | neg | high | low | low-med | partial | med-high |
| 12 | [52-week-high momentum](strategies/02-momentum/05-52-week-high-momentum.md) | B | mo | 0.3–0.5 | neg | high | med-low | med | partial | med |
| 13 | [Dual momentum (GEM)](strategies/02-momentum/06-dual-momentum-asset-allocation.md) | RP/B | mo | 0.5–0.7 | tail-cut | very high | trivial | trivial | modest | med |
| 14 | [Commodity CS momentum](strategies/02-momentum/07-commodity-cross-sectional-momentum.md) | RP/B | 1–12m | 0.3–0.6 | ~sym | med-high | low-med | med | partial | med-high |
| 15 | [Managed-futures trend](strategies/03-trend-following/01-managed-futures-trend.md) | RP/B | wks–mo | 0.4–0.7 | pos | very high | low-med | med | modest | highest |
| 16 | [Breakout/channel trend](strategies/03-trend-following/02-breakout-channel-trend.md) | RP/B | wks–mo | 0.3–0.6 | strong pos | high | med | low | as trend | med |
| 17 | [Trend + carry blend](strategies/03-trend-following/03-trend-plus-carry.md) | RP | wks–mo | 0.6–0.9 | ~neutral | very high | low | med | modest | high |
| 18 | [Short-term CS reversal](strategies/04-mean-reversion-swing/01-short-term-cross-sectional-reversal.md) | SF/C | days–wks | 0.3–0.7 | neg | low-med | binding | med | heavy raw; alive conditional | med-high |
| 19 | [Index panic mean-reversion](strategies/04-mean-reversion-swing/02-index-panic-mean-reversion.md) | SF | 2–15d | 0.4–0.7 | neg (stopped) | very high | trivial | low | mild | high |
| 20 | [Swing pullback-in-trend](strategies/04-mean-reversion-swing/03-swing-pullback-in-trend.md) | B+SF | 2–20d | 0.3–0.6 | mild pos | med-high | med | low | n/a (composition) | med |
| 21 | [Overnight/intraday decomposition ⚠](strategies/04-mean-reversion-swing/04-overnight-intraday-decomposition.md) | SF | sessions | 0.2–0.5 cond. | neg tails | high | extreme | med | naive dead | low-med |
| 22 | [FX carry](strategies/05-carry/01-fx-carry.md) | RP | mo | 0.2–0.4 raw; 0.4–0.6 filtered | strong neg | very high | low | low | substantial | med |
| 23 | [Commodity carry](strategies/05-carry/02-commodity-carry.md) | RP | mo | 0.4–0.7 | mild neg | med-high | med | high (chains) | partial | high |
| 24 | [Bond carry & roll-down](strategies/05-carry/03-bond-carry-rolldown.md) | RP | mo | 0.4–0.7 | mild neg | very high | low | med-high | mild-mod | med |
| 25 | [Volatility carry (VIX roll)](strategies/05-carry/04-volatility-carry-vix-roll.md) | RP | days–wks | 0.5–0.9 | extreme neg | med | low | low | moderate | high |
| 26 | [Cross-asset carry composite](strategies/05-carry/05-cross-asset-carry-composite.md) | RP | mo | 0.6–0.9 | neg diluted | very high | low | union of sleeves | alive @ haircut | high |
| 27 | [Variance risk premium ⚠](strategies/06-volatility/01-variance-risk-premium.md) | RP | wks–mo | 0.5–0.8 | most neg | high | high | very high (options) | compressed | med |
| 28 | [VIX term-structure trading](strategies/06-volatility/02-vix-term-structure-trading.md) | RP/SF | days–wks | 0.4–0.7 | ~neutral | med | low | low | moderate | med-high |
| 29 | [Dispersion ⚠](strategies/06-volatility/03-dispersion-index-vs-constituents.md) | RP/SF | 1–3m | 0.4–0.7 | neg | med | heavy | very high | cyclical | low-med |
| 30 | [Vol-targeting overlay](strategies/06-volatility/04-volatility-targeting-overlay.md) | C | daily | +0.1–0.3 to host | improves | unlimited | low | trivial | n/a | high (infra) |
| 31 | [PEAD](strategies/07-event-driven/01-post-earnings-announcement-drift.md) | B | wks–3m | 0.2–0.4 (0.4–0.7 small-cap) | mild | low-med | decisive | high (PIT earnings) | heavy large-cap | med |
| 32 | [Index rebalancing ⚠](strategies/07-event-driven/02-index-rebalancing.md) | SF | days–wks | niche | mixed | low-med | material | med | additions dead | low-med |
| 33 | [Buybacks & insider buying](strategies/07-event-driven/03-buybacks-and-insider-buying.md) | B | 3–12m | 0.4–0.7 | mild pos | med | light | med (public) | mild-mod | high |
| 34 | [IPO lockup expiry](strategies/07-event-driven/04-ipo-lockup-expiry.md) | SF/C | days–wks | 0.3–0.5 | neg (short) | low | high (borrow) | med | moderate | low-med |
| 35 | [Macro-announcement drift ⚠](strategies/07-event-driven/05-macro-announcement-drift.md) | RP | hrs–2d | 0.3–0.6 (A/C) | jumpy | very high | minimal | med (timestamps) | pre-FOMC dead | low-med |
| 36 | [CS equity value (+quality)](strategies/08-value-fundamental-factor/01-cross-sectional-equity-value.md) | RP/B | qtrs–yrs | 0.4–0.6 double-sort | slow droughts | very high | low | high (PIT fundamentals) | contested | high |
| 37 | [Cross-asset value](strategies/08-value-fundamental-factor/02-cross-asset-value.md) | RP/B | 1–5y | 0.3–0.5 | droughts | very high | negligible | med | moderate | med |
| 38 | [Low-vol / BAB](strategies/08-value-fundamental-factor/03-low-volatility-betting-against-beta.md) | C | mo | 0.3–0.5 LS; defensive LO | truncates | high | med (short leg) | low | moderate | med |
| 39 | [Turn-of-month / rebalancing flows](strategies/09-flows-seasonality/01-turn-of-month-rebalancing-flows.md) | SF | days | 0.3–0.6 | ~sym | very high | minimal | trivial | moderate | med-high |
| 40 | [Roll congestion ⚠](strategies/09-flows-seasonality/02-commodity-index-roll-congestion.md) | SF | 2-wk | ~0 now | spread | low-med | low | high | dead (naive) | low |
| 41 | [Fundamental seasonality](strategies/09-flows-seasonality/03-fundamental-seasonality.md) | SF/RP | wks–mo | 0.2–0.4/sleeve | mixed | med | low | med | mixed | low-med |
| 42 | [Perp funding-rate arbitrage](strategies/10-crypto-specific/01-perpetual-funding-rate-arbitrage.md) | C | continuous | cash+3–10% | neg (op tail) | med | med | low (public) | compressing/cyclical | high (crypto) |
| 43 | [Cross-exchange spot arb ⚠](strategies/10-crypto-specific/02-cross-exchange-spot-arbitrage.md) | C | min–days | low + episodic | op-neg | low-med | fees dominate | med | compressed | low-med |

## Cross-cutting findings

1. **Decay is the organizing fact.** ~50% average post-publication decay [X1]; four corpus strategies are documented deaths (index additions [E4], pre-FOMC [E6], naive overnight drift [R5], Goldman roll [S3-arc]). Rule of thumb by edge type: *price-pattern anomalies decay fastest; flow edges die when the flow adapts (datable); constraint edges compress as constraints relax; diversified risk premia persist at haircut levels because their losses are real.*
2. **Durability ranking of edge types:** risk premia (trend, carry, VRP, value) > constraint rents (low-vol, funding arb, converts) > behavioral anomalies (momentum flavors, PEAD, anchoring) > published flow patterns (index/TOM/roll). Allocate research and capital in that order.
3. **Costs decide sign at short horizons.** Reversal, PEAD, pairs — gross alpha exists; net alpha is a cost-engineering outcome. Every equity backtest must treat the cost model as first-class (mid-quote signals, one-day-wait tests, 2x-cost reruns).
4. **Negative skew is the price of "steady" returns.** Carry, VRP, merger arb, stat-arb, vol carry all sell some form of crash insurance and correlate in stress. The critique's cluster audit ([research/04-critique.md](research/04-critique.md) §3) reduces 43 docs to **~10–12 effective independent bets under stress correlations** — tail-budget them jointly, and pair with the corpus's positive-skew members (trend, breakout, panic-reversion playbook).
5. **The best portfolio skeleton from this corpus:** trend+carry futures book (≈ core) + equity factor sleeves (momentum/residual momentum + value+quality + defensive) + liquidity-provision sleeve (stat-arb/reversal, vol-conditional) + vol-carry satellite + event/flow satellites (buybacks-insiders, panic playbook, crypto funding if in scope) — all under a book-level vol target with the vol-targeting overlay module.
6. **Several "strategies" are really infrastructure:** vol-targeting overlay (30), announcement calendar (35), overnight decomposition diagnostics (21), and the seasonality multiplicity methodology (41) upgrade everything else regardless of standalone deployment.

## Recommended backtesting order

**Tier 1 — build first (core premia + reusable pipelines):**
1. Time-series momentum / managed-futures trend (9, 15) — one project; validates the futures pipeline (rolls, vol targeting).
2. CS equity momentum → residual momentum (8, 10) — validates the equity pipeline (survivorship, delisting, costs).
3. Vol-targeting overlay (30) as a module on both.
4. Commodity carry + momentum composite (23, 14), then trend+carry blend (17) and the carry composite (26, adding 22, 24, 25).

**Tier 2 — high-value satellites:**
5. Index panic mean-reversion (19) — cheap, high-capacity, episode playbook.
6. VIX carry → VIX term-structure state machine (25 → 28).
7. Buybacks & insider buying (33); equity value+quality (36) alongside (shared fundamental data).
8. Stat-arb residual portfolios (2) with short-term reversal (18) as its validation ground.
9. Crypto pair: funding arb (42) + cash-and-carry (3) if crypto is in scope.

**Tier 3 — conditional on data acquisition or niche interest:**
10. Merger arb (5, needs deal DB), PEAD (31, needs PIT earnings), VRP (27, needs options data), curve RV (6), cross-asset value (37), low-vol (38), TOM flows (39), dual momentum (13), 52w-high (12), industry/factor momentum (11), swing pullback A/B test (20), breakout (16).

**Tier 4 — studies, not deployments:** decayed set (32, 35-B, 21-D, 40) as decay-curve replications; dispersion (29), converts (7), lockups (34), cross-exchange arb (43), seasonality sweeps (41) as bounded research projects.

## Limitations & open questions

- Performance ranges are literature-derived estimates after standard haircuts, not backtest outputs — the next phase exists precisely to replace them with your numbers on your costs.
- Practitioner-sourced magnitudes (CTA/dispersion/CEF) rest on industry data not independently auditable here (critique §7).
- Crypto history spans ≤ 2 full cycles; all crypto expectations are regime-labeled.
- Excluded by scope: options market-making, credit RV beyond fallen angels, ML-signal strategies, discretionary macro — revisit if infrastructure ambitions change.
- Open questions worth their own research cycles: (a) does the announcement-day premium (35-A) survive the 2022–25 macro-vol regime? (b) how much of stock momentum does factor momentum subsume *in your universe* (11 vs 8)? (c) what is the current size of the deletion-reversion and fallen-angel residuals (32)?

## References

Full source log with credibility ratings: [research/01-landscape.md](research/01-landscape.md). Claim IDs ([X1], [M3], [C1], …) used throughout the strategy docs resolve there.
