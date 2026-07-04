# Commodity Cross-Sectional Momentum

## 1. Classification

- **Category:** Momentum (cross-sectional, commodity-specific)
- **Asset classes:** Commodity futures (energy, metals, agriculture, softs, livestock)
- **Style:** Long-short ranking across commodities
- **Horizon:** 1–12 month signals; monthly rebalance
- **Capacity:** Medium–high
- **Complexity:** Low–medium; **Data burden:** roll-adjusted futures series for 20–30 commodities

## 2. Economic rationale

Rank commodities against each other by trailing returns; long recent winners, short losers. Beyond generic underreaction, commodity momentum has a **physical backbone**: inventory cycles adjust slowly. A supply shock (drought, outage) draws down inventories over months; scarcity raises both spot prices *and* expected future returns (Gorton-Hayashi-Rouwenhorst [C5] show momentum winners are systematically **low-inventory** commodities). Price continuation reflects the slow mean reversion of physical inventories — production and consumption can't adjust quickly. Counterparty: hedgers on the wrong side of the shock (consumers hedging into rising scarcity) and index investors holding fixed weights regardless of inventory state. Overlaps heavily with commodity carry (low inventory ⇒ backwardation ⇒ positive carry) — the two signals are correlated cousins with a common physical cause; see §7 for the joint test.

## 3. Signal & rules specification

- **Universe:** 20–30 liquid commodity futures (WTI, Brent, gas, gold, silver, copper, aluminum, corn, wheat, soy complex, sugar, coffee, cotton, cattle, hogs…). Diversity across sectors matters — an energy-only book is one bet.
- **Signal:** trailing 12-month excess return (test 1, 3, 6, 12; commodity momentum is robust from ~3–12m; 12-1 skip not needed — commodity short-term reversal is weak).
- **Portfolio:** long top quartile / short bottom quartile (with ~25 markets: ~6 per side), **equal risk weights** (inverse ex-ante vol); sector caps (≤ 40% of risk per sector) to stop energy dominance.
- **Rebalance:** monthly; roll per market liquidity conventions (usually front or second contract, rolling 5–10 days pre-expiry, avoiding index-roll windows).
- Portfolio vol-target 8–12%.
- Recommended composite: average momentum z-score with carry z-score (slope of futures curve) — the literature and the physical logic both say these belong together.

## 4. Evidence & key research

- Miffre & Rallis (2007) [M11]: 13 momentum variants profitable in commodities, ~9%/yr for 12m ranking (1979–2004), uncorrelated to equities/bonds.
- Gorton, Hayashi & Rouwenhorst (2013) [C5]: momentum and backwardation both proxy inventory scarcity; momentum premium concentrated in low-inventory states — the mechanism evidence.
- Asness, Moskowitz & Pedersen (2013) [M2]: commodity momentum as part of "everywhere" evidence.
- Post-publication: commodity momentum weakened in the 2010s commodity bear (financialization + rangebound decade), strong again 2020–2022. Long-run premium estimate net: several % annually.
- **Decay status: partial;** physically-grounded mechanism argues for persistence, financialization argues for compression — the honest read is a ~40% haircut on published numbers.

## 5. Expected performance profile

- Net Sharpe: **0.3–0.6** standalone (diversified across ≥ 20 markets); near-zero correlation to equity/bond portfolios — diversification value is the headline.
- Skew: roughly symmetric to slightly positive (unlike equity momentum — commodity shorts don't have the high-beta-rebound crash anatomy).
- Turnover: moderate; costs low in liquid futures (1–3bp) but wider in ags/softs (model per-market).
- Watch: margin/vol spikes in squeezed markets (nickel 2022) — risk weights must use *stressed* vol.

## 6. Failure modes & risks

- Rangebound low-dispersion commodity regimes (2013–2019) → years of chop.
- Short-side squeeze risk: physical shorts can gap violently (frost, war, export bans); per-market position caps and stress-vol sizing are the defense.
- Roll congestion and index-flow interaction near roll windows.
- Correlated-with-carry: running both at full size double-counts one inventory bet (measure and budget jointly).

## 7. Backtesting guidance

- **Excess-return series from actual contracts** (see TSMOM doc §7): momentum on spot price series is a different (untradeable) result; the roll yield component is where much of the return lives.
- Include defunct/illiquid periods honestly (some markets were untradeably thin pre-1990s — apply ADV floors point-in-time).
- Test the inventory mechanism where data allows (EIA/USDA/LME stocks): momentum returns should concentrate in low-inventory names — a mechanism-validation test that guards against data-mined lookbacks.
- Joint test with carry: double-sort or regress momentum returns on carry returns; report the *incremental* Sharpe of momentum given carry — this number decides the allocation.
- Sample: 20y+ (must include 2008, 2014–15 oil crash, 2020–22).

## 8. Recommendations for use

- **Backtest priority: medium-high**, bundled with commodity carry (shared infrastructure, joint economics).
- Deploy as part of a commodity RV sleeve (momentum + carry composite, sector-capped, vol-targeted) inside the broader futures book alongside TSMOM.
- Its portfolio role: inflation-shock participation with two-sided positioning — one of the few sleeves that made money in both 2008 (short) and 2021–22 (long).
