# Cross-Sectional Equity Value (with Quality/Profitability Pairing)

## 1. Classification

- **Category:** Value / fundamental factor
- **Asset classes:** Equities (global)
- **Style:** Long-short factor (or long-only tilt); slow cross-sectional
- **Horizon:** Signal horizon quarters–years; monthly–quarterly rebalance
- **Capacity:** Very high
- **Complexity:** Medium (fundamental data handling); **Data burden:** point-in-time fundamentals + prices — the fundamental-data pipeline is the investment

## 2. Economic rationale

Cheap stocks (price low relative to fundamentals) outperform expensive ones over long horizons. Two compatible mechanisms: (a) **risk:** value firms are distressed-tilted, capital-inflexible, and suffer in bad times — the premium pays for that; (b) **behavioral:** investors extrapolate growth too far (gloomy for boring firms, euphoric for glamour), and prices mean-revert to fundamentals as expectations correct (Lakonishok-Shleifer-Vishny). Counterparty: growth-extrapolating investors and benchmark-constrained institutions. **Profitability/quality [F4] is the essential pairing, not an add-on:** cheapness alone loads on junk (value traps); "cheap given quality" (or "quality at a reasonable price") is the version with a coherent economic claim — buying productive assets below their worth, not just buying low multiples. Value and momentum are negatively correlated (~−0.4 [M2]) — the classic complementary pair.

## 3. Signal & rules specification

- **Universe:** top 1000–3000 by cap/liquidity, point-in-time; sector-aware.
- **Value composite (never a single ratio):** z-score average of book/price, earnings yield (trailing + forward if available), EBITDA/EV, free-cash-flow yield, sales/EV. Composite beats any single metric on robustness; B/M alone is the weakest modern choice (intangibles distortion — consider intangible-adjusted book).
- **Quality composite:** gross profitability (GP/Assets [F4]), ROE stability, accruals (low = good), leverage sanity.
- **Portfolio constructions to test:**
  1. Pure value long-short deciles (the academic benchmark);
  2. **Double sort:** long cheap-and-profitable / short expensive-and-unprofitable (the recommended production form);
  3. Long-only value+quality tilt vs benchmark.
- **Sector handling:** rank within sectors (valuation levels aren't comparable across them) — industry-neutral value is more consistent, though it forfeits occasional correct sector-level bets.
- **Rebalance:** monthly signal refresh, quarterly effective turnover (fundamentals move slowly); trade patiently (limit-style execution — the signal doesn't decay in a day).
- **Sizing:** vol-target; beta-neutralize the long-short (raw value shorts are low-beta expensive stable names — the book acquires unintended beta otherwise).

## 4. Evidence & key research

- Fama & French [F1]: HML across 90+ years US, replicated internationally; long-run premium ~3–5%/yr gross.
- Asness et al. [M2]: value works (with momentum) across 8 markets/asset classes.
- Novy-Marx [F4]: profitability as strong as value with opposite correlation profile; the double-sort logic.
- The 2018–2020 value winter: worst drawdown in factor history (~−50% for academic HML); Arnott et al. [F6] and Israel et al. [F7] decompose it — mostly *valuation-spread widening* (value got cheaper vs growth), not deterioration of the fundamental relationship; the subsequent 2021–22 value rebound followed the spread's partial normalization.
- **Decay status: contested.** Post-2007 US raw-B/M value ≈ flat for 15 years; composite+quality versions and non-US held up better; the McLean-Pontiff haircut applies, but the valuation-spread evidence argues the premium is cyclical-cheap, not dead. Position accordingly (modest expectations, long horizon).

## 5. Expected performance profile

- Net Sharpe: **0.2–0.4** pure value long-short; **0.4–0.6** value+quality double-sort; drawdowns are *multi-year* (the defining risk — not crashes but eras).
- Skew: value crashes slowly (unlike momentum's fast crashes); the pain is duration, not depth per day.
- Turnover: low (30–60%/yr) — the cheapest-to-trade equity factor; capacity effectively unlimited.
- Correlations: negative to momentum (pair them), positive to small-cap and (raw form) junk in recoveries.

## 6. Failure modes & risks

- **Regime droughts measured in years** (2007–2020) — career/behavioral risk dominates statistical risk; nobody gets fired for quitting value at the bottom, which is why the premium can exist.
- Value traps: secular decliners screen cheap forever (the quality pairing + accruals filter is the defense).
- Measurement rot: intangible-economy drift makes book value less meaningful each decade — composites and intangible adjustments are maintenance, not one-time fixes.
- Crowded unwinds at factor level (smaller than momentum's but real).

## 7. Backtesting guidance

- **Point-in-time fundamentals are non-negotiable:** as-reported data with availability lags (assume statements known 3–6 months after fiscal period end, or use vendor PIT stamps); restated-data backtests are systematically flattered.
- Survivorship-free with delisting returns (value's short leg and long leg both feature delistings — bankruptcies and takeovers respectively).
- Validate against published factors: your HML reconstruction should correlate > 0.9 with the published series before you trust variations.
- Report: pure value vs composite vs double-sort; sector-neutral vs raw; by decade; the 2018–2020 window isolated; valuation-spread time series (your monitoring instrument in production).
- Sample: as long as possible (40y+ preferred) — the premium's frequency content is decadal; short backtests are uninformative here.

## 8. Recommendations for use

- **Backtest priority: high** — not for near-term alpha excitement but because (a) the fundamental-data pipeline unlocks quality, buybacks (07-03), and defensive factors, (b) value is the designated diversifier for the momentum/trend-heavy rest of the corpus.
- Deploy as value+quality double-sort, sector-neutral, beta-hedged, at a size you can hold through a five-year drought — sizing for behavioral survivability *is* the strategy decision.
- Long-only variant is the natural personal-capital expression (tilt, not long-short).
