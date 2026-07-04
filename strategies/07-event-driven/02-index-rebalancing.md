# Index Add/Delete Rebalancing — ⚠ flagged: core effect largely decayed; niche expressions remain

## 1. Classification

- **Category:** Event-driven (structural flow)
- **Asset classes:** Equities (index changes), extendable to bond-index changes
- **Style:** Event trades around announcement → effective-date flow
- **Horizon:** Days–weeks per event
- **Capacity:** Low–medium (the surviving pockets are small)
- **Complexity:** Medium; **Data burden:** index change announcements (dates/terms), membership histories, prices

## 2. Economic rationale

Index funds must buy additions and sell deletions at the rebalance effective date, **price-insensitively** — a forecastable demand shock. Historically, front-running it (buy the addition at announcement, exit into the effective-date buying) earned 3–8% per event [E4]. The rationale is pure structural flow: the counterparty is the index fund's mandate itself (tracking error minimization forces trading at the close of effective day). **Why it mostly died [E4]:** (a) migrations between related indices (S&P 400↔500) now dominate — offsetting flows net out; (b) so much arb capital anticipates announcements (predicting additions before they're announced) that the post-announcement pop pre-empts to ~zero; (c) index funds got smarter about execution timing. Greenwood-Sammon: average S&P add effect ~0% in the 2010s–2020s.

**Surviving expressions:** (1) *deletion overshoot reversion* — deletions get oversold by the forced flow and revert over weeks (less arbitraged: requires warehousing an unloved small cap); (2) smaller/rules-based index families (Russell reconstitution pockets, thematic/smart-beta ETFs with mechanical rules and thin arbitrage); (3) *predictable-flow provision* — supplying liquidity at the effective-date close (selling additions into the closing auction, buying deletions there); (4) bond-index changes (fallen angels — see below).

## 3. Signal & rules specification

- **A. Deletion reversion:** at announcement of deletion (non-merger-related), short-term: expect further pressure into effective date; enter **long at effective-date close**; hold 20–60 days for reversion; stop on fundamental news. Historical edge: several % over the window; still measurable post-2010 in small deletions.
- **B. Russell reconstitution (annual, June):** rank-day membership is largely predictable from May market caps → predicted adds/deletes; trade the projected flow into reconstitution day and provide liquidity at the close. The classic version decayed; the residual is in the smallest-cap boundary names. Requires careful cost control.
- **C. Fallen angels (bond version, robust):** bonds downgraded from IG to HY are force-sold by IG-mandated funds and systematically revert over 6–12 months — documented premium (fallen-angel indices outperform HY broadly). Tradable via fallen-angel ETFs or bond selection; the *least decayed* index-flow effect because warehousing junk credit through a downgrade is genuinely unpleasant.
- **Sizing:** per-event risk ≤ 0.5%; these are many-small-events books (A/B) or a persistent tilt (C).

## 4. Evidence & key research

- Greenwood & Sammon (2024) [E4]: the definitive decay study — add effect 3.4% (1980s) → 7.4% (1990s) → ~0 (2010s); mechanisms: migrations, anticipation, better execution.
- Vijh (2022, *Financial Management*): recent S&P adds show ~*negative* announcement-to-effective returns some years — the arb is over-crowded.
- Deletion asymmetry: multiple studies (incl. [E4] decomposition) find deletion reversion persisted longer than addition premium.
- Fallen-angel literature (Ben Dor et al., Barclays/Bloomberg index research): ~2–5% annualized outperformance of fallen angels vs comparable HY over long samples — persistent.
- **Decay status: additions dead; deletions/fallen-angels/niche-index pockets alive.**

## 5. Expected performance profile

- A/B: modest — think **3–6% annualized on small deployed capital**, Sharpe hard to state (episodic, ~dozens of events/yr); C: a tilt worth 1–3%/yr over HY benchmark with credit beta.
- Skew: A is contrarian (buying forced-sale overshoot — positively skewed when it works, with fundamental-deterioration tail); C carries credit tails.
- Costs: material — the tradable names are small; closing-auction participation helps (trade *with* the auction liquidity event).

## 6. Failure modes & risks

- Trading a dead pattern: the addition premium — the backtest must be period-split or it will "discover" the 1990s.
- Deletions that deserved it (fundamental decliners): reversion fails; filter merger-/bankruptcy-driven deletions.
- Rule changes by index providers (announcement lead times, buffer rules) shift the game each era — regime-date your data.
- Crowding in the surviving pockets is ongoing; edges here erode on publication-speed timescales.

## 7. Backtesting guidance

- **Event database:** index change announcements with announcement date AND effective date (S&P/FTSE Russell press releases; membership history files). Period-split everything (pre-2000 / 2000–2010 / post-2010) — pooled results are misleading by construction here [E4].
- Measure separately: announcement→effective return, effective→+60d return (the reversion), per event type (add/delete/migration).
- Costs at small-cap reality (50–200bp round trip for the thin names); closing-auction fills modeled as achievable at close price.
- For fallen angels: downgrade dates point-in-time, bond or ETF total returns, credit-beta-adjusted benchmarking.
- The deliverable: a decay curve by era per expression — deciding what (if anything) is currently alive.

## 8. Recommendations for use

- **Backtest priority: low-medium** for equity add/delete (mostly a study in decay — valuable calibration for how fast structural edges die); **medium for fallen angels** (simplest robust survivor, ETF-tradable).
- If traded: deletion-reversion + fallen-angel tilt as small satellite sleeves; skip addition front-running entirely.
- Strategic value of the research: understanding index-flow mechanics feeds the flows/seasonality category (turn-of-month, roll congestion) — same family of price-insensitive counterparties.
