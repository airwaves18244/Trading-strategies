# Merger (Risk) Arbitrage

## 1. Classification

- **Category:** Arbitrage / relative value (event-driven RV; also cross-listed with event-driven)
- **Asset classes:** Equities (global M&A targets/acquirers)
- **Style:** Deal-spread capture, quasi-market-neutral
- **Horizon:** 1–12 months per deal (median ~3–4 months)
- **Capacity:** Medium–high
- **Complexity:** Medium (systematic version); **Data burden:** deal announcements database (terms, consideration type), daily prices, borrow for stock deals

## 2. Economic rationale

After a deal announcement, the target trades below the offer price. The gap (deal spread) compensates whoever holds the target through completion risk: regulatory block, financing failure, shareholder rejection, MAC events. Natural sellers are pre-announcement holders who have banked most of the premium and don't want event risk — they pay arbitrageurs to warehouse it. The return is a **risk premium with insurance-like structure**: collect many small spreads, occasionally eat a 15–40% loss when a deal breaks. Mitchell & Pulvino [A5] show the payoff is equivalent to **selling uncovered index puts**: in calm markets spreads are uncorrelated to equities; in crashes deals break simultaneously and the strategy inherits market beta exactly when it hurts.

## 3. Signal & rules specification

- **Universe:** announced, definitive (signed) deals above a size floor (e.g., target market cap > $500M); exclude rumors/indicative bids. US/EU/developed markets.
- **Per-deal inputs:** offer terms. Cash deal: spread `s = (offer − P)/P`. Stock deal (exchange ratio r): `s = (r·P_acq − P_tgt)/P_tgt`, traded as long target / short r·acquirer.
- **Annualized spread:** `s_ann = s · 365/expected_days_to_close` (use historical median close times by deal type/regulator involved as the baseline estimate).
- **Selection filter (systematic):** take deals where `s_ann` exceeds a hurdle (cash yield + 3–6%) but **exclude the extreme tail** (s_ann > ~25–30% signals the market pricing real break risk — these are bets, not carry; the naive "buy the widest spreads" portfolio underperforms).
- **Sizing:** loss-based: estimate downside-to-unaffected-price (pre-announcement price adjusted for market move since); size so a single break costs ≤ 0.5–1% NAV. Typical book: 15–40 concurrent deals, equal-risk weights.
- **Exits:** deal closes (collect spread); deal breaks (exit immediately — post-break drift is negative); spread widens > X% without news → reassess, don't mechanically add.
- **Rebalance:** event-driven; review book daily.

## 4. Evidence & key research

- Mitchell & Pulvino (2001) [A5]: 1963–1998, risk-arb portfolio ~4% annual excess over risk-free after realistic costs; Sharpe ~0.7–1.0 in calm regimes; payoff = short index put (market beta ~0.5 in down markets, ~0 in up markets).
- Baker & Savaşoglu (2002): limited arbitrage capital explains spread levels; returns higher when arb capital scarce.
- Live-era evidence: HFRI/merger-arb indices show ~3–5% annualized excess with low vol over 2000–2024; spreads widened dramatically in 2020 (COVID) and 2022–23 (aggressive antitrust) and paid well after.
- **Decay status: modest.** The premium compresses when capital floods in, re-widens after break clusters; it has persisted for 60 years because the insurance-like risk is real.

## 5. Expected performance profile

- Net returns: **cash + 2–5%** annually; Sharpe 0.6–1.0 in normal times.
- Skew: **strongly negative per deal** (win ~s, lose 10–40%); diversification across deals softens but crash-clustering of breaks means the book-level skew stays negative.
- Turnover: moderate, event-driven. Cost sensitivity: medium — spreads on targets are decent; the short acquirer leg in stock deals adds borrow cost and squeeze risk.

## 6. Failure modes & risks

- **Break clustering in crises:** financing-dependent deals die together (2008; COVID-March 2020). The strategy is short systemic risk — do not lever it as if uncorrelated.
- **Regulatory regime shifts:** antitrust aggressiveness (2021–2023 FTC/DOJ era) raised break rates on large strategic deals; a backtest calibrated on 2010s break rates underestimated risk. Deal-mix awareness (horizontal megadeals vs PE take-privates) matters.
- Bidding wars help (positive tail: topped bids), hostile/rumor situations hurt — the definitive-deal filter is load-bearing.
- Stock-deal shorts: acquirer squeezes, dividend/ratio adjustments, borrow recalls.

## 7. Backtesting guidance

- **Data is the hard part:** you need a point-in-time deal database — announcement date/time, terms and amendments, consideration mix, completion/termination dates and outcomes. Sources: SDC/Refinitiv, Bloomberg MA<GO>, or hand-built from press releases for a smaller sample. Without amendment history, backtests mis-price renegotiated deals.
- Enter at next-day open after announcement (never announcement-day close without checking timestamp), use unaffected prices for downside estimation.
- Model breaks properly: on termination, mark the target at the actual post-break price path (day+1 close), not at the unaffected price.
- Include borrow cost on acquirer shorts; model ratio adjustments and dividends on both legs.
- Report by deal type (cash/stock/mixed), by size, and by regulatory intensity; check the Mitchell-Pulvino nonlinearity by regressing monthly P&L on market returns in up vs down months — a correct implementation reproduces the short-put shape.
- Sample: ≥ 300 deals across ≥ 2 stress episodes.

## 8. Recommendations for use

- **Backtest priority: medium** — logic is well-established; the real question is your data access. If no deal database is available, defer rather than approximate.
- Portfolio role: carry-like income sleeve, diversifying vs trend/momentum but **not** vs short-vol strategies (same crash factor as VRP, stat-arb — budget them jointly).
- Practical tilt for a smaller book: cash deals, mid-cap targets, definitive agreements, hurdle-based selection with tail exclusion.
