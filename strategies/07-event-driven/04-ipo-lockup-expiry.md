# IPO Lockup Expiration (Supply-Shock Event)

## 1. Classification

- **Category:** Event-driven (predictable supply shock)
- **Asset classes:** Equities (recent IPOs; SPAC variants)
- **Style:** Short-side event trade (+ long reversion tail)
- **Horizon:** Position days–weeks around a *known calendar date*
- **Capacity:** Low (recent IPOs; borrow-constrained)
- **Complexity:** Medium; **Data burden:** IPO dates + lockup terms (prospectus data), borrow availability/fees, prices

## 2. Economic rationale

IPO insiders (founders, VCs, employees) are contractually locked up, typically 90–180 days post-IPO. At expiry, a large block of shares (often 3–10× the float) becomes sellable, and holders with concentrated, low-cost-basis positions (VCs with distribution mandates, diversifying employees) predictably sell. Field & Hanka [E8]: average **−1.5% abnormal return** in the expiry week, permanent ~40% volume increase, worse for VC-backed firms — remarkable because the date is public information the day the prospectus prints; the persistence is a **limits-of-arbitrage rent**: shorting recent IPOs is expensive (borrow scarce, fees high, squeeze risk in glamour names), so the anticipated selling isn't fully pre-arbitraged. Counterparty: locked-up insiders' mechanical liquidity demand meeting a thin post-IPO market.

Secondary expression: post-expiry *reversion* — once the supply overhang clears (weeks after), oversold names with strong fundamentals recover; and the expiry date often marks the start of institutional accumulation (index/fund eligibility timelines).

## 3. Signal & rules specification

- **Event calendar:** for each IPO, lockup expiry date(s) from the prospectus (watch multi-tranche lockups and early-release triggers — modern deals often stagger).
- **A. Short into expiry:**
  - Universe: IPOs 4–7 months old with (a) VC/PE-heavy ownership, (b) large locked-share-to-float ratio (> 2×), (c) big run-up since IPO (unrealized gains = selling propensity), (d) **borrow available at < 5–10% fee** (the binding filter).
  - Entry: short 5–10 trading days before expiry; exit day +2 to +5 after (the pressure window); stop at +8–10% adverse (squeeze protection).
- **B. Post-overhang long (reversion):** names down > 20% into/through expiry with intact fundamentals (revenue growth, cash) — long from day +5–10, hold 1–3 months.
- **Sizing:** small per event (0.3–0.5% risk) — single-name IPO vol is extreme; 10–30 events/yr in normal issuance regimes; the book is episodic and issuance-cyclical.
- Hedge: short leg vs IPO-sector ETF or index to isolate the event from growth-stock beta.

## 4. Evidence & key research

- Field & Hanka (2001) [E8]: −1.5% expiry-week abnormal return across 1,948 lockups (1988–1997); 3x larger for VC-backed; volume permanently higher.
- Ofek & Richardson (2000), Brav & Gompers (2003): confirm; conclude limits-to-arbitrage (borrow constraints) sustain it.
- Later evidence: magnitude attenuated in the 2010s (staggered lockups, early releases, more sophisticated positioning) but event-window abnormal returns remain measurable, especially in high-run-up, high-locked-ratio cohorts; 2020–21 IPO/SPAC wave provided a large fresh sample (SPAC lockup dynamics even stronger due to sponsor-share economics).
- **Decay status: moderate;** structural persistence argument (borrow costs) intact but deal-structure innovation keeps changing the details — event terms must be read per deal.

## 5. Expected performance profile

- Per-event edge: ~1–3% over the window historically, before borrow fees (which can eat half); hit rate modest (~55–60%) with occasional −10%+ squeezes — a many-small-bets book.
- Net Sharpe: **0.3–0.5** in active-issuance years; near-dormant when IPO markets freeze (2022–23) — capacity and opportunity are issuance-cyclical.
- Skew: negative on the short side (squeeze tail), positive on the reversion side.
- Costs: **high** — borrow fees are a first-class input, not an afterthought.

## 6. Failure modes & risks

- **Squeezes in crowded shorts:** everyone sees the same calendar; heavily-shorted expiries can rip on any positive news (the trade's known tail).
- Early lockup releases / secondary offerings pre-expiry (the supply arrives on a different date than modeled — track amendments).
- Borrow recall mid-trade.
- Regime dependence: in raging bull markets insider selling gets absorbed (2020: many expiries rallied through).

## 7. Backtesting guidance

- Build the event dataset from prospectuses/vendor IPO calendars: IPO date, expiry date(s), locked shares, float, ownership type — the data assembly is most of the project; SPACs need their own term parsing.
- **Borrow realism decides the result:** without historical borrow-fee data, bound it — assume fee tiers by name-type (recent hot IPO: 5–50%+) and show results by fee assumption; a version ignoring borrow is upper-bound fiction.
- Abnormal returns vs growth/IPO-sector benchmark; report by cohort (VC-backed, run-up tercile, locked-ratio tercile) reproducing the [E8] cross-sectional pattern as validation.
- Sample: needs an issuance wave or two — 2013–2015, 2019–2021 (+SPACs) are the modern cohorts.

## 8. Recommendations for use

- **Backtest priority: low-medium** — a specialist niche: capacity-light, data-assembly-heavy, but one of the clearest *structural supply* events for studying flow-driven pricing; strong learning-to-capital ratio, small capital fit.
- Trade only borrow-cheap events, hedged, small; the reversion long (B) is friendlier to run than the short (A) for accounts with expensive shorting.
- Natural bundle with other supply/flow events (index deletions doc 07-02, month-end flows category 09) as a "flow events" sleeve.
