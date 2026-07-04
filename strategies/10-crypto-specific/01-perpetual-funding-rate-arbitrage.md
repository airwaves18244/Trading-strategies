# Perpetual Funding-Rate Arbitrage (Crypto Carry)

## 1. Classification

- **Category:** Crypto market structure (carry/arbitrage hybrid)
- **Asset classes:** Crypto perpetual swaps vs spot (BTC/ETH core; alts extension)
- **Style:** Delta-neutral funding capture
- **Horizon:** Continuous; funding accrues every 1–8h; positions held days–months
- **Capacity:** Medium (BTC/ETH), low (alts)
- **Complexity:** Medium; **Data burden:** funding-rate histories + perp/spot prices per venue (public APIs)

## 2. Economic rationale

Perpetual swaps track spot via the **funding mechanism**: when perp > spot (longs dominant), longs pay shorts a periodic funding rate; when perp < spot, shorts pay longs [K1][K2]. Retail and momentum-chasing leverage demand is structurally **long-biased** in crypto bull phases, so funding is positive most of the time and spikes double-to-triple-digit annualized in manias. The arbitrage: **short the perp, long equal spot** → delta ≈ 0, collect funding. Economically identical to cash-and-carry (doc 01-03) but continuous: the trader supplies leverage to retail longs and is paid their impatience premium. Counterparty: levered directional traders; the edge persists because supplying it requires capital on (risky) exchanges, operational competence, and tolerance for the mechanism's tail (funding flips negative in crashes exactly when exchange risk peaks) — a classic constraint-based rent, compressing as institutional capital enters [K3] but regenerating each retail-leverage cycle.

## 3. Signal & rules specification

- **Instruments:** perp short + spot long on the same venue (cleanest margining) or across venues (better rates, more risk); stablecoin-margined perps preferred (linear P&L; coin-margined adds convexity complications).
- **Entry signal:** trailing funding (e.g., 7-day average annualized) > hurdle = stablecoin yield + operational risk premium (suggested 8–12% annualized hurdle; test 5–20%). Current-epoch funding alone is too noisy; predicted funding (premium-based formula per exchange [K2]) helps timing.
- **Exit:** trailing funding < exit threshold (e.g., < 5% ann.) or negative for > 2–3 days; capital returns to yield.
- **Cross-venue/cross-asset allocation:** rank venues/assets by funding; concentrate in top rates subject to per-venue caps (counterparty budgeting: ≤ 25–35% of strategy NAV per offshore venue) — the cross-sectional version of the trade.
- **Sizing/margin:** the short-perp leg loses mark-to-market in rallies while spot gains sit elsewhere → **keep perp margin utilization ≤ 25%** at entry; auto-deleverage/liquidation must be impossible up to a 2x adverse move; rebalance margin between legs on schedule.
- **Alt extension:** higher funding, higher spread/borrow/liquidity risk — separate risk bucket, position caps tiny.

## 4. Evidence & key research

- Ackerer, Hugonnier & Jermann [K1]: perp pricing/no-arbitrage framework; funding as the tether to spot.
- Exchange specs [K2]: funding formulas — premium component + interest differential; clamps and intervals differ by venue (design details matter to P&L timing).
- Live risk/return studies [K3]: 2024–25 analyses show funding-arb returns of ~5–15% annualized net in normal regimes, spiking to 30%+ in manias (2021-H1, late-2023–early-2024), with rates ~0.015%/8h standard in expansion phases; institutionalization (basis funds, ETF-era plumbing) visibly compressing average levels vs 2020–21.
- Makarov & Schoar [K4]: the general result — crypto arbitrage rents persist where capital/venue frictions bind.
- **Decay status: structurally compressing, cyclically regenerating.** Long-run trajectory is toward the cash-and-carry basis's fate (low single digits over cash), but each retail-mania cycle re-fattens it for months at a time.

## 5. Expected performance profile

- Blended expectation: **stablecoin yield + 3–10%** annualized through-cycle; deployed-capital Sharpe high in opportunity windows (P&L is quasi-carry), punctuated by operational-tail events.
- Skew: negative — steady collection vs rare venue failures (FTX-2022 class), negative-funding stretches, and execution slippage in crash exits.
- Turnover: low; costs = entry/exit spreads and fees on two legs + rebalancing — meaningful for short deployments (amortize by holding through the window).

## 6. Failure modes & risks

- **Exchange/counterparty risk dominates** (identical to doc 01-03 §6): FTX wiped positions regardless of trade correctness. Venue caps, minimal idle balances, and preference for venues with proof-of-reserves/regulated status are the actual risk management.
- Funding inversion in crashes: funding flips negative while spreads blow out — exit costs peak with stress; the exit rule must tolerate a few negative days rather than panic-close at the wides.
- Basis gap between legs (perp vs your spot venue) widening at rebalance times; stablecoin depeg risk on margin collateral (USDC Mar-2023).
- Liquidation mechanics: a violent rally with slow margin rebalancing liquidates the short before spot gains can be moved — the margin-utilization cap is the strategy.

## 7. Backtesting guidance

- Funding histories are public per venue (APIs) — assemble per asset/venue since 2019–2020; backtest = accrual simulation: funding received − fees/spreads − borrow (if any) − margin-rebalancing costs, with the entry/exit rules applied to trailing funding.
- **Simulate the margin path** through actual price series (as doc 01-03 §7): flag any margin breach under the utilization cap as a design failure.
- Haircut for counterparty risk explicitly (e.g., X% annual probability of losing venue-resident capital, sensitivity-tested) — a spreadsheet line that changes conclusions.
- Report per-cycle: 2020–21 mania, 2022 bear (negative-funding stress), 2023–24 recovery, 2025 institutionalized regime — the compression trend is the key output for forward expectations.
- Include the cross-venue dispersion series [K3]: is the cross-sectional version worth its extra counterparty surface?

## 8. Recommendations for use

- **Backtest priority: high within crypto** (if crypto is in scope at all): the best risk-adjusted crypto-native strategy for a non-HFT operator, with public data and a few days of backtest work.
- Deploy as the crypto cash-enhancement sleeve twinned with doc 01-03 (same capital can rotate between dated basis and perp funding by richness); counterparty budgeting before yield optimization, always.
- Natural companion to crypto trend (doc 03-02 variant): funding is richest precisely when trend is long — the pair monetizes manias twice, delta-neutral and directionally.
