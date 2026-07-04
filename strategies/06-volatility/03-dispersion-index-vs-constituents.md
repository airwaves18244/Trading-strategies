# Volatility Dispersion (Index vs Constituents) — ⚠ flagged: options data, multi-leg complexity

## 1. Classification

- **Category:** Volatility (correlation risk premium)
- **Asset classes:** Index options vs single-stock options (SPX/top-50 names canonical)
- **Style:** Vega-neutral relative value: short index vol / long single-name vol
- **Horizon:** 1–3 month structures
- **Capacity:** Medium
- **Complexity:** Very high (highest in corpus with convertibles); **Data burden:** full options chains for index + dozens of names — flagged

## 2. Economic rationale

Index variance = weighted average single-name variance × average pairwise **correlation**. Index implied vol trades systematically rich relative to constituent implied vols — equivalently, **implied correlation exceeds realized correlation** on average. Cause: institutional hedging happens overwhelmingly at the *index* level (cheapest, fastest), pushing index IV up, while single-name vol supply (covered-call writers, dealers warehousing idiosyncratic risk) keeps constituent IVs relatively cheap. The dispersion trade — sell index options, buy a vega-weighted basket of single-name options — is **short correlation**: it profits when stocks move on their own (idiosyncratic dispersion) and loses when everything moves together (crashes, when correlation → 1). It is therefore another crash-insurance premium, but with a distinctive engine: the structural index-hedging flow imbalance [V8]. Counterparty: index-protection buyers (pensions, structured products) and single-name vol sellers.

## 3. Signal & rules specification

- **Structure (baseline):** short SPX straddles/strangles (30–60 DTE), long straddles on top 30–50 constituents, **vega-weighted** so net portfolio vega ≈ 0; delta-hedged both legs (or use variance-swap-like strips for purity).
- **Signal/conditioning:** implied correlation `ρ_imp = (σ²_idx − Σw²σ²_i) / (Σ_{i≠j} w_i w_j σ_i σ_j)` (or use published implied-correlation indices, e.g., COR3M). Enter when ρ_imp is in its upper historical quantiles (≥ 60–80th percentile) and expected dispersion is high (earnings seasons, macro-quiet + micro-active regimes); stand down when ρ_imp already cheap.
- **Ratio discipline:** classic sizing is notional/vega-weighted; gamma-weighted variants behave differently in crashes — decide and document.
- **Risk rules:** scenario cap on correlation → 1 shock (index vol +15pts, correlation to 0.9): loss ≤ 5% NAV; earnings-calendar management on single-name legs (long single-name vol *collects* on earnings surprises — a feature, but concentrate expiries around earnings consciously).
- **Cadence:** monthly ladder; hold 3–6 weeks; unwind before final-week gamma.

## 4. Evidence & key research

- Driessen, Maenhout & Vilkov [V8]: correlation risk premium documented — index options embed a premium over constituents explained by priced correlation risk; dispersion strategies earn it.
- Implied-vs-realized correlation spread: persistently positive on SPX (typical gap ~5–15 correlation points) — published dealer research and the COR index history corroborate.
- Practitioner reality: a dispersion desk staple for decades; returns strong in stock-picker regimes (2000–2007, 2021 single-name mania), poor in macro-lockstep regimes (2008–2012 risk-on/risk-off).
- **Decay status: cyclical, structurally supported** — the index-hedging flow imbalance regenerates; crowding shows up as compressed implied-correlation premium (observable → the conditioning variable *is* the crowding meter).

## 5. Expected performance profile

- Net Sharpe: **0.4–0.7** conditioned; unconditioned always-on dispersion ≈ 0.3 with brutal 2008-type months.
- Skew: negative (short correlation = short crash), partially offset by long single-name vol collecting on idiosyncratic blowups.
- Costs: **heavy** — dozens of option legs, spreads on single names 2–10x index spreads; execution quality is a first-order return driver. Turnover moderate.

## 6. Failure modes & risks

- **Correlation spikes:** systemic events send ρ → 1; the short-index-vol leg dominates and the trade behaves like naked short vol precisely then.
- Single-name leg selection: skipping names (partial baskets) adds tracking noise; over-weighting high-IV names embeds a short-quality tilt.
- Operational complexity: 50+ legs, delta hedges, earnings calendar — errors are P&L.
- Margin: multi-leg portfolios margin badly at retail brokers; realistically a portfolio-margin/institutional strategy.

## 7. Backtesting guidance

- Needs the full options-data stack (OptionMetrics-class) for index + names; realistic spreads per leg (this kills most paper edges — model 30–50% of quoted spread paid per leg).
- Simplified proxy backtest first: **implied-correlation z-score → variance-swap approximation** (index var strip vs weighted single-name var strips at mid) to establish whether the premium timing works before modeling leg-level fills.
- Reports: P&L vs realized-correlation outcomes (the mechanism check), performance by ρ_imp entry quantile, 2008/2020 months isolated, cost sensitivity at 2x spreads.
- Sample: 2005+ (good single-name chains); two correlation regimes minimum.

## 8. Recommendations for use

- **Backtest priority: low-medium** for an independent quant — the edge is real but execution- and data-gated; study it to understand correlation premia even if not deploying.
- If deployed: conditioned entries only (ρ_imp expensive), defined-risk wings on the index leg, top-liquidity names only.
- Portfolio note: it hedges *nothing else in this corpus* (short crash like the other vol/carry sleeves) — its diversification claim vs VRP is about idiosyncratic-dispersion regimes, worth a small satellite at most.
