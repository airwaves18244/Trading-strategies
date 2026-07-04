# Futures Cash-and-Carry Basis Arbitrage

## 1. Classification

- **Category:** Arbitrage / relative value (deterministic-ish carry to expiry)
- **Asset classes:** Crypto (main live opportunity), equity index futures, commodities (specialists), historically FX
- **Style:** Market-neutral basis capture
- **Horizon:** Hold to futures expiry (weeks–months) or basis normalization
- **Capacity:** Medium–high (crypto), high (index futures, but spread ≈ 0 there)
- **Complexity:** Low–medium; **Data burden:** daily futures + spot prices; funding/borrow rates

## 2. Economic rationale

A future must price at spot + cost of carry: `F = S·e^{(r + storage − yield)τ}`. When `F` trades rich, buy spot / short future, deliver (or cash-settle) at expiry, and the annualized basis is locked in **regardless of price path**. The mispricing exists when the marginal buyer of the future cannot or will not hold spot: in crypto, leveraged longs prefer futures/perps, and regulated funds pay a premium for futures exposure (basis spiked >20% annualized in bull phases — 2021, 2024). The seller of the basis provides **balance-sheet and leverage** to speculators; compensation is for capital lockup, counterparty/exchange risk, and margin path risk. In mature markets (equity index, FX) arbitrage capital has compressed the basis to the financing rate — nothing left for outsiders; in crypto the constraint (few players with cheap balance sheet willing to hold coins on exchanges) still binds, though institutionalization since the 2024 ETF era has compressed it too.

## 3. Signal & rules specification

Crypto implementation (the tradable one):

- **Universe:** BTC, ETH dated futures (quarterlies) on major venues (CME for the regulated version; offshore exchanges carry higher counterparty risk premium — which *is* part of the spread).
- **Signal:** annualized basis `b = (F/S − 1)·(365/days_to_expiry)`. Enter when `b > hurdle`, where hurdle = your stablecoin/cash yield + estimated all-in costs + a risk premium (suggested hurdle: cash yield + 3–5%; range to test 2–10%).
- **Trade:** long spot (or spot ETF) + short the future, notionally matched. Hold to expiry (guaranteed convergence) or exit early if basis compresses to ≤ cash yield (capture realized, redeploy).
- **Sizing:** limited by margin path risk on the short-futures leg — in a rally, the short loses mark-to-market while spot gains are unrealized/on another venue. Keep futures margin utilization ≤ 25–35% at inception; size so a 2x price move doesn't force liquidation.
- **Variant:** perp-based version = funding-rate arbitrage (separate doc, `10-crypto-specific/01`); dated-futures version trades convergence certainty against lower average yield.
- **Rebalance:** roll at expiry into the richest tenor if still above hurdle; otherwise sit in cash.

## 4. Evidence & key research

- Textbook no-arbitrage relation; documented crypto basis episodes: annualized BTC quarterly basis reached 20–40% in 2021-H1 and 15–25% in early 2024; compressed to low single digits in bear phases (public exchange data; [K1], [K4]).
- Makarov & Schoar (2020) [K4]: persistence of crypto arbitrage spreads is explained by capital mobility frictions — the spread is rent to those who pre-position capital.
- Equity index basis: post-2010, index futures basis ≈ implied financing ± single bps; academic work on the "futures-cash basis" finds dealers' balance-sheet costs (post-Basel III) drive small persistent richness — capturable only by institutions with cheap funding.
- **Decay status:** crypto basis structurally compressing as institutions enter (CME OI growth, ETF creation/redemption plumbing), but re-opens every bull phase; equity/FX basis fully decayed decades ago.

## 5. Expected performance profile

- Return = basis captured; historically lumpy: 10–30% annualized during bull-market entry windows, ~cash yield otherwise. Long-run expectation: **cash + 3–8%** with disciplined hurdles, near-zero market beta.
- Sharpe on deployed capital during opportunity windows: 2+ (the P&L is quasi-deterministic once on); blended Sharpe depends on how often the hurdle is met.
- Skew: mildly negative — small steady carry vs rare counterparty/operational losses.
- Turnover: low. Cost sensitivity: low–medium (few trades; but crossing spreads on both legs at entry/exit matters for short tenors).

## 6. Failure modes & risks

- **Counterparty/custody risk is the real risk:** exchange failure (FTX 2022 wiped out basis traders' collateral), withdrawal freezes. Mitigate: CME + spot ETF version, or multi-venue with minimal idle balances. Understand that the fat basis on offshore venues is *pay for this risk*.
- **Margin path risk:** short futures leg in a violent rally → forced liquidation before convergence turns a locked profit into a loss. This killed under-collateralized carry traders in 2021.
- **Basis inversion (backwardation):** in crashes, futures trade below spot; entering "rich basis" positions late in a bull market means marking losses as basis mean-reverts violently.
- Stablecoin/fiat rails risk for the cash leg; regulatory changes on crypto ETF/futures access.

## 7. Backtesting guidance

- Backtest is mostly a **historical opportunity census**, not a signal test: reconstruct the annualized basis series per venue/tenor (beware: use synchronized timestamps for F and S — crypto trades 24/7, CME doesn't; unsynchronized quotes fabricate basis).
- Model margin dynamics explicitly: simulate the mark-to-market path of the short leg through the actual price path; count any margin breach as a forced exit at that day's basis.
- Include: taker/maker fees both legs, withdrawal fees, stablecoin conversion, and (offshore) a haircut for counterparty risk — e.g., assume loss of collateral with small annual probability and check the strategy still clears the hurdle.
- Data: daily settlement prices for quarterlies (CME public; exchange APIs for offshore history), spot index prices. 2019+ covers two full cycles.

## 8. Recommendations for use

- **Backtest priority: medium** (simple to validate; the research question is "how often does the hurdle trigger and what's the realistic all-in yield", not "does the logic work").
- Best used as an **opportunistic cash-enhancement sleeve**: capital sits in T-bills/stablecoin yield and deploys when basis blows out. Pairs naturally with a crypto trend allocation (basis is richest exactly when trend is long).
- Non-negotiable operational rule: counterparty risk budgeting before yield maximization.
