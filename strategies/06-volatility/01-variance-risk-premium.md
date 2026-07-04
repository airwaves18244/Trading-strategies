# Variance Risk Premium Harvesting (Delta-Hedged Short Options) — ⚠ flagged: options data & infrastructure

## 1. Classification

- **Category:** Volatility (the foundational vol premium)
- **Asset classes:** Index options (SPX core); single-stock, rates, FX, commodity options as extensions
- **Style:** Delta-hedged short volatility
- **Horizon:** Option tenors 2 weeks–3 months; continuous hedging
- **Capacity:** High (index); **Complexity:** High
- **Data burden:** **options chains (quotes, greeks) + underlying — flagged; heaviest ongoing data need after convertibles**

## 2. Economic rationale

Implied volatility systematically exceeds subsequently realized volatility on equity indices (~3–4 vol points average on SPX, positive ~85% of months [V1][V6]). Selling options and delta-hedging isolates this gap: the hedged seller earns (IV² − RV²) in variance terms, independent of direction. Why the premium persists: option buyers are **insurance buyers** — institutions hedging tail risk, structured products, regulatory-driven protection demand — and they knowingly overpay, exactly as home-insurance buyers do; the seller's losses concentrate in crashes when marginal utility is highest, so the premium is genuine risk compensation, not mispricing [V1][V2][V3]. It's the equity market's most fundamental non-directional premium; VIX carry (doc 05-04) and dispersion (06-03) are its listed-futures and cross-sectional derivatives.

## 3. Signal & rules specification

Systematic baseline (index, defined-risk preferred):

- **Structure:** short **delta-hedged straddles/strangles** on SPX, 30–45 DTE, or short variance via listed var-replicating strips. For non-institutional risk control: **iron condors / short strangles with bought wings** (defined risk) accepting lower premium capture.
- **Entry cadence:** ladder — open a new position weekly (tenor diversification), hold to ~50–75% premium capture or ~7–10 DTE, then close/roll (avoid gamma-heavy final week unless specifically harvesting it).
- **Delta hedging:** band-based (re-hedge at ±5–10 delta) with index futures; wider bands = more P&L noise, less cost.
- **Conditioning (documented improvements):**
  - Size ∝ current **VRP estimate**: IV (e.g., VIX or ATM IV) minus a realized-vol forecast (EWMA/HAR); skip entries when estimated VRP ≤ 0 — selling vol below its forecast cost is uncompensated;
  - Reduce/skip into scheduled macro events (CPI/FOMC) or price them consciously;
  - Hard vega/gamma caps: portfolio loss at an instant −10% index gap + IV +15pts scenario ≤ 5–8% NAV.
- **Sizing:** vol premium sleeve ≤ 10–15% of book risk; margin headroom ≥ 3x normal requirement (stress margin expansion is a forced-exit mechanism).

## 4. Evidence & key research

- Carr & Wu [V1]: variance swap rates >> realized variance across indices; premium concentrated in equity indices (weaker/absent in some FX/commodities).
- Bakshi & Kapadia [V2]: delta-hedged option gains negative for buyers (= sellers earn premium), systematic across strikes.
- Bollerslev et al. [V3]: VRP as priced state variable.
- Practitioner records: CBOE PUT/BXM indices (systematic put-selling/buy-write) — long-run equity-like returns with lower vol *pre-cost*, real but modest net premium; short-vol funds' 2018/2020 blowups [V4] mark the tail.
- **Decay status: compressed but persistent** — the premium narrowed post-2018 (better-priced tails, more sellers) yet remains positive on average; the insurance logic guarantees it can't fully vanish while hedging demand exists.

## 5. Expected performance profile

- Net Sharpe: **0.5–0.8** for conditioned, defined-risk index versions; raw undefended short-vol prints higher until a crash removes years of P&L.
- Skew: **the most negative in this corpus** — that's the product being sold; monthly win rate 80%+, tail months −10–25% even with wings if oversized.
- Turnover/costs: continuous hedging costs + option spreads are material; index options are the only liquid-enough venue for small operations.

## 6. Failure modes & risks

- **Gap + vol explosion:** simultaneous large underlying move and IV spike (the short position loses on gamma and vega at once) — Feb-2018, Mar-2020. Defined-risk wings and the scenario cap are the survival spec.
- Margin spiral: exchanges raise margins in stress → forced covering at the wides (the mechanism that converts drawdown to ruin).
- Realized-vol clustering: losses persist across weeks in vol regimes (not one bad day); the VRP-conditioning reduces exposure then.
- Correlation with everything: short-vol crashes when equities crash — it adds tail weight to a typical book; budget jointly with carry/merger-arb/stat-arb sleeves.

## 7. Backtesting guidance

- **Options data is the gating decision:** you need historical chains with bid/ask (OptionMetrics/ORATS/CBOE DataShop; SPX from ~1996, good quality 2005+). Without it, run doc 05-04 (VIX carry) instead — same premium, futures data.
- Fill realism: sell at bid / buy at ask (or mid ± 25–40% of spread); hedge fills at futures spread; include hedging frequency sensitivity.
- Simulate margin: SPAN-style stress margin through 2008/2018/2020 — flag any forced-liquidation breach as strategy failure, not a drawdown.
- Reports: P&L decomposition (theta/vega/gamma/hedging), worst-10 episodes, wings on/off comparison, VRP-conditioning on/off, and the PUT/BXM benchmark comparison.
- Sample: must span 2008 *or* 2020 **and** 2017 (the lowest-vol year — tests whether returns exist when VRP is thin).

## 8. Recommendations for use

- **Backtest priority: medium** — high knowledge value, but gated on options data acquisition; do VIX carry (05-04) first and this second as the deeper expression.
- Deploy defined-risk only at ≤ 10% of book risk, with the gap-scenario cap as the binding constraint and pre-committed no-averaging rules.
- Strategic role: the "insurance underwriting" income sleeve of the book — must be paired with positive-skew allocations (trend) and never levered to make its calm-year income look like a core return stream.
