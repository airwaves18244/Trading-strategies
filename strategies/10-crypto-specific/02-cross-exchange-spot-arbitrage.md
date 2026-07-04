# Cross-Exchange Crypto Spot Arbitrage (Non-HFT Variant) — ⚠ flagged: execution-reality-dependent

## 1. Classification

- **Category:** Crypto market structure (fragmentation arbitrage)
- **Asset classes:** Spot crypto across venues (and geographic premia)
- **Style:** Market-neutral spread capture
- **Horizon:** Minutes–days (slow dislocations), not sub-second (that's the HFT tier — out of scope)
- **Capacity:** Low–medium
- **Complexity:** Medium-high operationally; **Data burden:** multi-venue price/orderbook history (public APIs); fee/withdrawal schedules

## 2. Economic rationale

Crypto trades on dozens of fragmented venues with **no consolidated tape, no NBBO, and slow/costly inter-venue settlement** (blockchain withdrawals take minutes–hours; fiat rails take days). Price differences persist beyond fee bounds because closing them requires **pre-positioned capital on both venues** (inventory on the cheap venue's quote currency, coins on the rich venue) plus operational tolerance for venue risk [K4]. Makarov-Schoar: arbitrage spreads of tens of bps to whole percents persisted for *days–weeks*, especially **cross-border** (the "kimchi premium" — Korea trading 5–50% rich in 2017–18 — rooted in capital controls; won-rail frictions are the moat). The non-HFT edge is not speed: it's **capital pre-positioning and rail access** — being already there when dislocations open. Counterparty: locally-captive demand (regional retail waves) and anyone paying immediacy on a thin venue. The sub-second tier is fully professionalized [K3: only ~40% of top spread observations survive costs]; the surviving non-HFT game is the slow, structural, and episodic dislocations.

## 3. Signal & rules specification

- **Universe:** BTC/ETH + majors across 3–6 venues you can actually operate (KYC'd accounts, tested rails); optionally one geographic-premium pair where you have legal rail access.
- **Monitoring:** consolidated spread matrix `d_{ij} = P_i/P_j − 1` net of taker fees both sides; alert when net spread > threshold (e.g., > 30–50bp for majors — rare; sizing to the persistence [K3, K4]).
- **Execution (pre-positioned inventory model):** hold X% capital as stablecoin on venue A and coins on venue B; on signal: buy on cheap venue, sell on rich venue *simultaneously* (no transfer in the trade loop — transfers happen later, off-critical-path, to rebalance inventory). The transfer-in-the-loop version (buy → withdraw → deposit → sell) bears price risk for the transfer duration and is only worth it for large, slow premia.
- **Inventory rebalancing:** scheduled, netted, during calm periods; count withdrawal fees/times per asset (use fast-settlement assets as the shuttle where sensible).
- **Risk rules:** per-venue capital caps (counterparty budgeting as docs 01-03/10-01); max inventory imbalance; kill-switch on venue withdrawal suspensions (the canonical trap: the rich venue is rich *because* withdrawals are broken — check before trading, not after).
- **Sizing:** edge-proportional, bounded by top-of-book depth on the thinner venue; this is a small-capital-friendly, capacity-limited strategy.

## 4. Evidence & key research

- Makarov & Schoar (2020) [K4]: the definitive study — large, persistent cross-venue/cross-border deviations; arbitrage index spikes in retail-demand waves; capital controls explain the geography.
- [K3] (2025): 17% of observations show ≥ 20bp spreads but only ~40% of top opportunities survive costs+reversal — the modern, compressed reality on major pairs; CEX→DEX information flow one-directional (CEX leads).
- Live structure: major-pair cross-venue spreads in 2024–25 normally < 5–10bp (dead for slow traders); dislocations reopen in vol events (Mar-2020: multi-percent spreads for hours; FTX collapse week; regional regulatory shocks).
- **Decay status: heavily compressed on majors in calm regimes; episodic and geographic residuals persist** where capital/rails frictions bind [K4's mechanism is structural].

## 5. Expected performance profile

- Honest expectation: **low single-digit annualized on committed capital in normal regimes; episodic multi-percent weeks in dislocations** — the return distribution is a trickle plus spikes correlated with crypto vol events.
- Skew: positive-ish per trade (defined capture), negative operationally (venue-failure tail dwarfs accumulated edges if caps ignored).
- Costs: fees dominate (maker/taker tiers decide viability); withdrawal fees and rail costs on rebalancing.

## 6. Failure modes & risks

- **Venue failure with inventory aboard** — the dominant risk, again (FTX; regional exchange collapses); the strategy's whole design is counterparty-risk budgeting with an arbitrage attached.
- Broken-rail premia (rich venue = frozen withdrawals): the spread is a trap, not an edge — rail-status checks are part of the signal.
- One-legged fills in fast markets (bought cheap, rich side moved) → unintended inventory; simultaneous-execution discipline and depth-bounded sizing.
- Regulatory/KYC changes closing rails mid-position (geographic trades especially).
- Stablecoin pricing asymmetries across venues masquerading as crypto spreads (price in consistent quote terms).

## 7. Backtesting guidance

- **A backtest here is an opportunity census + operational simulation**, not a signal optimization: reconstruct synchronized multi-venue top-of-book (public trade/quote archives; beware timestamp skew across APIs — clock-align or the "spreads" are artifacts), net out fee schedules per venue-tier, and count opportunities by size/duration/venue-pair.
- Simulate the inventory model: capital split, rebalancing costs/latencies, and how much of each historical dislocation your depth-bounded size could actually capture.
- Segment by regime (calm vs vol events) and by pair type (major-major, major-regional); the deliverable is a table: *expected annual capture per $100k committed, by venue set* — a capital-allocation answer, not a Sharpe.
- Include the failure weeks (Mar-2020, Nov-2022) both as opportunity and as counterparty-risk case studies.

## 8. Recommendations for use

- **Backtest priority: low-medium** — worth the census to know the opportunity's current size; deploy only if the numbers clear your operational-risk bar and the capital has no better use in docs 01-03/10-01 (which usually dominate on risk-adjusted terms and share the infrastructure).
- If run: pre-positioned inventory model only, small, venue-capped, with rail monitoring automated; treat it as paid readiness for dislocation events rather than a steady business.
- Strategic value: the venue/rail/operational infrastructure it forces you to build is exactly what the other crypto sleeves (01-03, 10-01, 03-02-crypto) run on.
