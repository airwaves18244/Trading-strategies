# Cross-Asset Carry Composite (Global Carry)

## 1. Classification

- **Category:** Carry (multi-asset composite; the category's production form)
- **Asset classes:** FX, commodities, bonds, equity indices, volatility (+ crypto funding) — one book
- **Style:** Cross-sectional and time-series carry per class, risk-balanced across classes
- **Horizon:** Monthly (weekly for vol/crypto legs)
- **Capacity:** Very high
- **Complexity:** Medium-high (aggregation of 4–6 sleeves); **Data burden:** union of docs 05-01…05-04 (+10-01)

## 2. Economic rationale

Koijen-Moskowitz-Pedersen-Vrugt [C1] showed **carry is one concept everywhere**: define carry as the return an asset earns if prices stay unchanged (futures curve roll, rate differential, dividend yield minus financing, vol curve roll-down, perp funding), and it predicts returns *within every asset class tested*. The deep rationale: every market has natural hedgers/liquidity demanders paying to shed a risk, and the carry measure is the visible price of that insurance. Crucially, **carry premia across classes are nearly uncorrelated** (different payers, different crash triggers: FX carry crashes on risk-off, commodity carry on supply shocks, bond carry on hiking cycles, vol carry on equity crashes) — so the composite earns the average premium at a fraction of the component risk. Diversification across *insurance types* is the entire design; equity-index carry (dividend/futures basis) is the weakest documented sleeve and optional.

## 3. Signal & rules specification

- **Sleeves:** FX carry (doc 05-01 spec), commodity carry (05-02), bond carry (05-03), vol carry (05-04), optional crypto funding (10-01), optional equity-index carry (futures basis vs dividends — small weight if used).
- **Per-sleeve:** each built exactly per its doc (with its filters — valuation for FX, deseasonalization for commodities, etc.); normalized to a target vol (e.g., 5% each).
- **Aggregation:** risk-parity across sleeves (equal ex-ante vol contribution), with tail-budget override: cap combined **crash-correlated** sleeves (FX carry + vol carry + any short-skew leg) at ≤ 40% of book risk — their calm-market correlation understates joint tails.
- **Portfolio vol target:** 8–12%; rebalance monthly (vol/crypto sleeves weekly).
- **Blend recommendation:** the full production form combines this composite with trend per doc 03-03 — carry alone is the negative-skew half of the pair.

## 4. Evidence & key research

- Koijen et al. [C1]: global carry factor across 9 classes, gross Sharpe ~1.1 (1983–2012), positive in every class; carry crashes correspond to global liquidity/downturn events but class-level premia diversify substantially.
- Component evidence: [C2–C8], [V5], [K1–K3] per sleeve docs.
- Post-publication: component-level decay differs (FX heavy [C4], commodity/vol partial, bond mild) — a live composite over 2013–2025 would have earned well below the in-sample 1.1 but remained positive and diversifying; practitioner multi-asset carry funds (public track records) net Sharpe ~0.5–0.8 over the period.
- **Decay status: composite premium alive at haircut levels;** the diversification result (low cross-sleeve correlation) has held out-of-sample, which is the design's real claim.

## 5. Expected performance profile

- Net Sharpe: **0.6–0.9** for the 4–6 sleeve composite (vs 0.2–0.7 per sleeve) — diversification, not heroics.
- Skew: negative but *diluted*; worst weeks are global risk-off events where 2–3 sleeves crash together (Aug-2024, Mar-2020) — hence the tail-budget cap.
- Turnover: low; aggregate costs small (futures/forwards).
- Correlation: low to equities/trend in normal times; positive to equities in liquidity crises (own it consciously).

## 6. Failure modes & risks

- **Global carry unwind:** the correlated-tail event across sleeves; the composite's diversification is weakest exactly when needed most — sizing must assume sleeve correlations → 0.7 in stress, not the calm-period ~0.1.
- Component spec errors compound silently (a seasonality bug in commodity carry pollutes the composite) — validate sleeves independently first.
- Over-engineering risk: weight optimization across sleeves on 30 years of data = fitting a handful of crash episodes; use risk parity + tail cap, nothing fancier.

## 7. Backtesting guidance

- **Sequenced build:** each sleeve validated per its own doc → composite as a thin aggregation layer. Never debug the composite directly.
- Reports that matter: sleeve correlation matrix (calm vs stress subsamples), composite vs best-single-sleeve Sharpe (the diversification claim), joint-crash table (worst 20 composite weeks with sleeve attribution), and the trend-blend comparison (doc 03-03).
- Stress correlations: recompute sleeve correlations in the worst equity-vol decile — this number drives honest sizing.
- Sample: constrained by the shortest sleeve (VIX futures 2004+, crypto 2019+) — run a long 3-sleeve composite (FX/commodity/bond, 25y+) and a short full composite (2010s+) separately.

## 8. Recommendations for use

- **Backtest priority: high as the category capstone** (after sleeves pass individually).
- This composite + trend (03-01/03-03) + equity factor sleeves is the skeleton of a complete systematic macro book; carry composite ≈ 20–30% of total risk with the tail cap enforced.
- Resist adding sleeves with undocumented carry definitions — the concept's strength is that each sleeve's payer is identifiable; carry you can't attribute to a payer is probably a data artifact.
