# Convertible Bond Arbitrage — ⚠ flagged: data- and infrastructure-heavy

## 1. Classification

- **Category:** Arbitrage / relative value (cross-instrument, volatility-linked)
- **Asset classes:** Convertible bonds vs their underlying equities (+ credit hedges)
- **Style:** Delta-hedged long-volatility-and-credit RV
- **Horizon:** Months–years per position
- **Capacity:** Medium (issuance-limited market)
- **Complexity:** High; **Data burden:** heavy — convertible terms & prices (OTC), borrow, credit spreads, equity vol. **Flag: hardest data requirement in this corpus.**

## 2. Economic rationale

A convertible = straight bond + equity call option (+ issuer-specific features). Converts chronically issue **cheap to theoretical value** because issuers (often mid-cap, capital-hungry) pay a discount for speed and covenant-light capital, and the natural buyer base is narrow. The arbitrageur buys the convert, shorts delta of the underlying stock, and hedges rates/credit as desired — monetizing the cheapness through (a) gamma trading the hedge as the stock moves, (b) carry (coupon + short rebate − borrow), (c) cheapness convergence. Compensation: providing capital to a segmented issuer market and bearing liquidity/deleveraging risk — the strategy's losses concentrate in funding crises when the leveraged holder base unwinds together (1998, 2005, 2008 [A6]).

## 3. Signal & rules specification

- **Universe:** outstanding converts above size/liquidity floor; new issues (systematically cheapest — the "new-issue discount" is a documented 2–4% average).
- **Valuation:** price each convert with a standard model (binomial/PDE with credit spread, call features, dividends). Signal = market price vs model value: buy cheapness > 2–4% with borrowable stock.
- **Hedging:** short model delta in the stock; rebalance on delta bands (±5–10 delta points) rather than daily-fixed — band width is the gamma-P&L/cost tradeoff. Optional: hedge credit (CDS) and rates (futures) to isolate vol+cheapness.
- **Sizing:** per-issuer ≤ 2–3% NAV; leverage historically 2–6x in funds — for independent operation ≤ 1.5–2x. Diversify ≥ 20 names.
- **Exit:** cheapness closed, borrow lost, credit deterioration beyond threshold, or issuer calls/converts.

## 4. Evidence & key research

- Mitchell & Pulvino (2012) [A6]: convert-arb returns are compensation for liquidity provision; in 2008, forced deleveraging pushed converts to ~10–15% below theoretical value — buyers with stable capital earned outsized returns in 2009.
- Agarwal, Fung, Loon & Naik (2011): convert-arb funds' returns largely explained by buying-cheap-new-issues + hedging factors.
- Long-run fund indices: mid-single-digit net returns, Sharpe ~0.7–1.0 outside crises, with 2008 drawdowns of −30%+ for levered funds.
- **Decay status: cyclical, not secular.** Cheapness compresses when arb capital is abundant, blows out in crises; the 2020–21 issuance wave re-fattened the opportunity, 2022 rates repricing hurt, 2023–25 normalized.

## 5. Expected performance profile

- Net returns: **cash + 3–6%** at moderate leverage; Sharpe ~0.7 through-cycle.
- Skew: negative (liquidity-crisis drawdowns), with strong post-crisis recoveries — same "short funding liquidity" factor as stat-arb/merger-arb.
- Turnover: low–medium. Cost sensitivity: high — OTC bond spreads, borrow fees, and financing terms dominate small cheapness edges.

## 6. Failure modes & risks

- **Deleveraging spirals:** the holder base is levered funds on prime-broker financing; margin tightening → forced sales → more cheapness → more margin calls (2008 anatomy [A6]). Survive by low leverage and term financing — or accept you're paid for this exact risk.
- Borrow loss on the equity short (takeover bids on the issuer are ironically painful: convert gains capped by terms, short loses).
- Model risk: credit-equity correlation in distress (delta explodes as stock → 0); call/put/covenant misreads.
- For an independent quant: **access risk** — bond minimums, financing, and OTC data may make this untradeable in practice; that's why it's flagged.

## 7. Backtesting guidance

- Honest statement: a fully faithful convert-arb backtest requires convertible terms + daily OTC prices + historical borrow — vendor data (ICE/Refinitiv) is expensive. Feasible fallbacks:
  1. **New-issue-discount study:** collect new-issue terms (public prospectuses), model value at issue, measure cheapness-convergence over 3–6 months — a bounded, high-signal project.
  2. **Proxy replication:** long convert ETFs/indices vs delta-matched short equity index + long credit hedge — tests the *factor*, not the security selection.
- Model at least: bid-ask 50–150bp on bonds, borrow 25–500bp, financing at broker rates; haircut model values by feature complexity.
- Include 2008 and March 2020 in any sample; report unlevered returns first.
- Minimum data: convert terms database, daily bond marks, equity prices/borrow — or use fallback designs above.

## 8. Recommendations for use

- **Backtest priority: low** for an independent quant (data/access constraints), **included for completeness** of the RV map and because the liquidity-provision factor it isolates recurs across this corpus.
- If pursued: new-issue systematic buying with delta hedging is the practical entry point; or express the view via convert funds/ETFs when cheapness (published by dealers) is extreme.
- Portfolio role: overlaps with stat-arb/merger-arb crisis factor — do not stack all three at high leverage.
