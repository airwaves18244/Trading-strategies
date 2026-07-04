# Bond Carry & Roll-Down (Rates Carry)

## 1. Classification

- **Category:** Carry (rates/fixed income)
- **Asset classes:** Government bond futures across countries/tenors; swaps for institutions
- **Style:** Time-series per-market and cross-sectional across countries/curve points
- **Horizon:** Monthly rebalance; slow-moving signal
- **Capacity:** Very high
- **Complexity:** Medium; **Data burden:** bond futures + yield-curve data (zero/par curves per country)

## 2. Economic rationale

A bond's expected excess return if the curve doesn't move = **carry (yield − funding) + roll-down** (price gain as the bond ages into a lower-yield curve segment when the curve is upward-sloping). Positioning where carry+rolldown is fat is compensated **term-premium harvesting**: investors demand extra yield to bear duration risk, and the premium varies over time and across markets. Who pays: (a) short-horizon safe-asset demanders (banks' liquidity portfolios, FX reserve managers, pension liability hedgers) who hold front-end/specific tenors regardless of value, creating segmented richness; (b) borrowers issuing long duration. The steepness signal works because term premia are persistent: steep curves have predicted high bond excess returns for a century (with regime caveats — steepness sometimes reflects expected hikes that *do* materialize, the strategy's loss mode).

## 3. Signal & rules specification

- **Universe:** liquid bond futures: US (2y/5y/10y/30y), Germany (Schatz/Bobl/Bund/Buxl), UK, Japan, Australia, Canada… — 10–20 contracts across ~8 countries.
- **Carry measure per contract:** `carry+roll = (y_tenor − funding_rate) + (dy/dτ)·Δτ_horizon` estimated from the local curve; for futures directly: expected futures price drift under an unchanged curve (standard practitioner computation from CTD forward yield vs spot yield).
- **Time-series rule:** long where carry+roll > 0, short where < 0, signal size ∝ z of the measure; **cross-sectional rule:** long the richest-carry markets/tenors vs short the poorest, duration-neutral overall if you want pure carry (or duration-positive if harvesting term premium outright — decide and document; they are different strategies).
- **Rebalance:** monthly; positions in **risk (DV01) space**, inverse-vol weighted; portfolio vol target 6–10%.
- **Curve-RV expression:** within-country steepener/flattener where roll differentials across tenors are extreme (2s10s carry-adjusted) — the rates version of doc 01-06.
- **Regime caution flag (not a timing model):** carry signals performed poorly in fast hiking cycles (2022) — a simple trend-blend (doc 03-03) is the documented fix rather than a bespoke filter.

## 4. Evidence & key research

- Koijen et al. [C1]: bond carry (both across countries and across maturities) positive, Sharpe ~0.5–0.9 in-sample per sleeve.
- Cochrane & Piazzesi (2005) [C7]: forward-rate combinations forecast bond excess returns — the academic backbone of time-varying term premium.
- Ilmanen [X4/C7]: long-sample evidence on curve steepness → subsequent excess return across countries.
- Live check: rates carry had a strong 2010s (steep curves, no hikes materializing), a disastrous 2022 (carry long into the fastest hiking cycle in 40 years — steepness was *not* a premium but a correct forecast), recovering 2023–25.
- **Decay status: mild-to-moderate;** the payer base (liability hedgers, reserve managers) is structural, but QE/QT eras manipulate the signal's meaning — regime awareness required.

## 5. Expected performance profile

- Net Sharpe: **0.4–0.7** diversified across countries/tenors; correlation to equities low but **not** crisis-safe in inflation shocks (2022: bonds and equities fell together — this strategy was long duration into it unless trend-blended).
- Skew: mildly negative; drawdowns come as sustained repricing episodes (1994, 2013 taper, 2022) rather than crashes.
- Turnover: low; futures costs tiny; capacity effectively unlimited at this corpus's scale.

## 6. Failure modes & risks

- **Hiking-cycle repricing:** steepness reflecting correctly-anticipated hikes → carry longs lose on both legs (2022 anatomy).
- QE/QT distortions: central banks buying duration compress term premia and the signal's information content; policy regime shifts flip relationships abruptly.
- Cross-country carry embeds FX decisions: hedge FX (pure rates carry) or accept an implicit FX carry overlay — specify explicitly; unhedged versions double-count FX carry risk (doc 05-01).
- CTD switches and delivery-option quirks in futures (technical, handleable).

## 7. Backtesting guidance

- Compute carry+roll from actual curves (vendor zero curves or bootstrapped from futures/CTD yields) — do not proxy with "yield level" alone; roll-down is half the signal.
- Futures excess returns roll-adjusted; DV01-space positioning; FX-hedge the cross-country sleeve.
- Report performance by policy regime (hiking/cutting/QE eras) — the strategy's honest brochure is regime-split, not pooled.
- Include 1994 (if data), 2013, 2022; test trend-blend (doc 03-03) vs raw carry — expected result: blend rescues the 2022-type mode.
- Data: 20y+ futures + curves across ≥ 6 countries.

## 8. Recommendations for use

- **Backtest priority: medium.** Solid diversifier inside the futures risk-premia book; rarely worth running standalone.
- Deploy blended with trend (the 2022 lesson is structural: rates carry needs a change-sensitive partner); FX-hedged, DV01-budgeted.
- The within-curve RV variant is a good specialization if rates become a focus area; otherwise the cross-country TS version inside the composite suffices.
