---
title: "Critique — Red-Team Pass"
project: trading-strategies-research
flow: universal
phase: 4
date: 2026-07-04
---

# Phase 4 — Critique / Red-Team Pass

Per universal.md Phase 4: hunt bias, cherry-picking, causal leaps, missing counter-evidence; verify convergent evidence isn't a single source chain. Findings below; where a finding required correction, the strategy docs already incorporate it (this pass was run before finalizing).

## 1. Single-source-chain audit

- **Trend/TSMOM cluster (docs 02-02, 03-01, 03-02, 03-03):** much of the headline evidence traces to one intellectual lineage — AQR-affiliated authors (Moskowitz, Ooi, Pedersen, Hurst, Asness) across [M2][M3][T1][T3][C1]. This is a genuine chain risk: the firm sells these strategies. **Mitigations present:** independent confirmation from Baltas-Kosowski [T2] (academic, non-AQR), live index data [T6] (SG, independent), and the hedging-pressure literature [T5]. Verdict: evidence stands, but published Sharpe from this chain should be read as marketing-adjacent upper bounds — the docs' 30–50% haircuts are appropriate, not conservative.
- **Carry evidence** similarly Koijen-Moskowitz-Pedersen-centric [C1]; FX-carry decay evidence [C4] and crash anatomy [C2][C3] are independent chains — adequately triangulated.
- **Overnight-drift decay** rests partly on a practitioner blog [R5]; docs rate it L→M and cross-check against [R3][R4] rolling data. Acceptable for a decayed-strategy flag (the claim argues *against* trading, so the bias risk is benign).
- **Crypto funding-arb magnitudes** [K3 + web sources]: some 2025-era claims (e.g., "215% capital increase", "AI execution −40% slippage") come from low-credibility marketing content surfaced in search; **these specific numbers were excluded from the strategy docs** — only [K1][K3][K4]-grade claims were used.

## 2. Survivorship of "known" anomalies / cherry-picking check

- The corpus deliberately includes **four strategies documented as decayed or dead** (index additions 07-02, pre-FOMC 07-05-B, naive overnight drift 04-04, Goldman roll 09-02) with their decay curves as the deliverable. This is the anti-cherry-picking control: the same methodology that supports live strategies is shown killing dead ones.
- Every category doc carries an explicit decay-status line grounded in [X1] (~50% average post-publication decay) — no strategy is presented at in-sample magnitude.
- Residual concern: the corpus's *selection* still tilts toward strategies famous enough to be published — genuinely proprietary edges are absent by construction. The backtesting phase should expect published-strategy net Sharpe at the *low* end of stated ranges.

## 3. Independence / overlap audit (the "≥25 independent approaches" claim)

Strategies that must NOT be counted as independent (documented in each doc, aggregated here):

| Cluster | Docs | Shared engine |
|---------|------|---------------|
| Momentum family | 02-01, 02-03, 02-04, 02-05 | Underreaction/continuation — one risk allocation |
| Trend family | 02-02, 03-01, 03-02, 02-06 | Time-series continuation — one allocation |
| Liquidity provision | 01-01, 01-02, 04-01, 04-02 | Inventory-risk compensation; crowding-crash common factor |
| Short-crash-insurance | 01-05, 05-01, 05-04, 06-01, 06-03 (+01-07) | All sell tail insurance; correlations → high in stress |
| Carry family | 05-01…05-05, 10-01, 01-03 | Hedging-pressure/impatience premia (though cross-class carry diversifies well [C1]) |
| Flow events | 07-02, 07-04, 09-01, 09-02 | Price-insensitive-flow front-running/provision |

Counting clusters + genuinely distinct singletons (merger arb's deal risk, value's expectation-reversion, low-vol's leverage constraint, PEAD's information diffusion, insider signals, VRP, dispersion's correlation premium, funding arb's venue rents, ETF-NAV stress provision, curve RV's storage bounds, seasonality's physical cycles, vol-targeting's variance forecastability…), the corpus contains **~28–30 economically independent return sources** across 43 documents — the brief's ≥25 threshold is met, but a portfolio built from all 43 docs has ~10–12 *effective* independent bets once stress correlations are honored. SUMMARY.md carries this forward.

## 4. Causal-leap check

- **Swing pullback (04-03):** the composition claim (trend premium + reversal premium ⇒ pullback-in-trend works) is a hypothesis, not a published result — doc explicitly labels it medium-confidence and specifies the A/B kill test. Compliant.
- **Breakout logic (03-02):** anchoring evidence [M5] supports level-breach information content indirectly (it's about equities, applied to futures) — the doc leans primarily on the estimator-equivalence result [T4], which is solid. Acceptable with the noted inference gap.
- **Panic mean-reversion (04-02):** "majority of −3σ moves reverted" is a stylized statistic, not a cited table — flagged: the backtest must generate the episode census itself; the doc's design (episode-level analysis) already demands this.
- **TOM "explains all equity premium" [S1/McConnell-Xu]:** striking in-sample decomposition, and window instability post-2015 is real — doc appropriately demands rolling-window evidence before deployment.

## 5. Performance-number sanity check

- All stated Sharpe ranges were cross-checked for internal consistency: no strategy doc promises net Sharpe above ~1.0 standalone; composites (trend+carry, global carry) top out at 0.6–0.9 — consistent with the best public institutional track records. Anything higher in the source literature (e.g., [C1]'s 1.1 gross, [M10]'s doubled Sharpe) is quoted as gross/in-sample with the haircut stated.
- Negative-skew strategies (carry, VRP, merger arb, vol carry) all carry explicit tail-event enumerations (1998, 2008, Feb-2018, Mar-2020, Aug-2024) — no "smooth returns" presentation survives the docs.

## 6. Missing counter-evidence — added during this pass

- Momentum: the 2010s US raw-momentum dry spell is stated in 02-01 (not just the crashes).
- Value: the 2018–2020 −50% HML drawdown and the "is value dead" debate [F6][F7] are foregrounded, not footnoted.
- Vol targeting: Cederburg et al. critique included in 06-04 (out-of-sample gains smaller for market portfolios).
- Low-vol: Novy-Marx-Velikov implementability critique included in 08-03.
- Dual momentum: live-era (2015–2025) underperformance documented in 02-06 rather than only the book-sample results.

## 7. Remaining known weaknesses (accepted, disclosed)

1. Several practitioner-sourced magnitudes (CTA live Sharpe, dispersion desk returns, CEF discount premia) rest on index/industry data that can't be independently audited here — marked M-credibility and ranges kept wide.
2. Crypto docs rely on a short history (≤ 2 full cycles) — all crypto expectations are labeled regime-dependent.
3. The corpus contains no options-market-making, no credit RV beyond fallen angels, and no ML-signal strategies — scoping choices (data/infrastructure realism for a non-HFT independent operator), not oversights.
4. Backtest feasibility ratings assume the user's stated data plan (daily + some intraday); strategies flagged ⚠ (convertibles 01-07, VRP 06-01, dispersion 06-03, index rebalancing 07-02, roll congestion 09-02, macro drift 07-05, cross-exchange arb 10-02, overnight 04-04) carry their gating caveats in-file.

**Gate verdict:** corpus passes Phase 4 with the above disclosures. Proceed to Phase 5 report.
