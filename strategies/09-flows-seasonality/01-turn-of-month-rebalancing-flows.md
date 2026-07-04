# Turn-of-Month & Month-End Rebalancing Flows

## 1. Classification

- **Category:** Flows & seasonality (calendar-flow structural)
- **Asset classes:** Equity indices (primary), bonds (the rebalancing counter-leg)
- **Style:** Calendar-conditional exposure
- **Horizon:** ~4–8 trading-day windows monthly
- **Capacity:** Very high (index futures)
- **Complexity:** Low; **Data burden:** daily index/futures data only

## 2. Economic rationale

Two related calendar-flow effects with identifiable payers:

1. **Turn-of-month (TOM) [S1]:** a disproportionate share of equity returns historically accrues in the window from ~the last trading day through the first ~3 days of the month. Mechanism: synchronized cash flows — payrolls, pension contributions, 401(k) purchases, fund inflows — hit equities on a monthly rhythm; dealers/liquidity providers pre-position for it. McConnell-Xu: the effect explains essentially *all* of the US equity premium in their long sample (equities earned ~nothing outside the TOM window, 1926–2005 — an astonishing decomposition).
2. **Month-end institutional rebalancing [S2]:** pensions/target-allocation funds rebalance to fixed weights near month-end → after equities outperform bonds intra-month, they *sell* equities/buy bonds at month-end (and vice versa). Etula et al.: predictable price pressure in the last days and its **reversal in the first days**; the flow size is forecastable from intra-month relative performance.

Counterparty: mechanical, calendar-locked flows (retirement systems, allocation mandates) that trade regardless of price. The persistence argument: these flows are institutional plumbing, slow to change — though the effects have attenuated as they've been arbitraged and as flows diversified across dates.

## 3. Signal & rules specification

- **A. TOM harvest:** long index futures from close of T−1 (last trading day −1) through close of T+3 of each month; flat (or in T-bills) otherwise. Parameter window to test: entry T−4…T−1, exit T+2…T+5. This is an exposure-timing strategy: ~20% of days, historically most of the return.
- **B. Rebalancing-pressure trade [S2]:** signal = intra-month equity-minus-bond relative return through day ~T−5. If equities strongly outperformed (> +2–3%), expect month-end equity *selling*: short/underweight equities vs long bonds over the last 2–3 days, unwind (or reverse long) in the first 2–3 days of the new month (the reversal leg). Symmetric for bond outperformance.
- **C. Quarter-end amplification:** the same logic amplified at quarter-ends (bigger rebalancing programs); test as conditioning variable rather than separate strategy.
- **Sizing:** vol-scaled index/bond futures positions; overlay-scale (≤ 10% of book risk); costs negligible.

## 4. Evidence & key research

- Lakonishok & Smidt (1988), McConnell & Xu (2008) [S1]: TOM effect across 90 years, all size deciles, and most of 34 international markets; not explained by risk measures examined.
- Etula, Rinne, Suominen & Vaittinen (2020, *RFS*) [S2]: month-end/turn reversal patterns tied directly to measured institutional liquidity needs; economically significant in equities and bonds.
- Post-publication: TOM attenuated in recent US decades (still positive in most rolling windows, smaller magnitude); the rebalancing-pressure signal [S2] is newer with less public decay evidence; 2020s anecdotes (huge quarter-end rebalances in Mar-2020, 2022) confirm the flow mechanism at scale.
- **Decay status: TOM moderate decay; conditional rebalancing-pressure version comparatively fresh.** Both must be treated as regime-monitored overlays.

## 5. Expected performance profile

- A: historically captured most of the equity premium at ~20% exposure — modern expectation: **1–3%/yr timing value** with big year-to-year variance; Sharpe of the pattern 0.3–0.6.
- B: **0.3–0.5 Sharpe** as a small overlay; per-event edges of 20–50bp on the pressure/reversal round trip in strong-signal months.
- Skew: A holds equities through known-flow windows (normal equity tails apply on those days); B is two-sided and roughly symmetric.
- Costs: minimal (index futures, few trades/month).

## 6. Failure modes & risks

- **Flow migration:** T+1 settlement changes, payroll-date diversification, and smarter execution by institutions shift the windows — parameters drift on multi-year scales; rolling-window monitoring is part of the spec.
- Crowding: both patterns are published; front-running the front-runners compresses and can inverts timing by a day or two.
- Event collisions: FOMC/CPI landing in the TOM window dominates the flow effect (calendar-aware risk from doc 07-05 applies).
- B's signal is a proxy (actual rebalancing flows unobserved) — months with offsetting flows (new mandates, redemptions) produce false signals.

## 7. Backtesting guidance

- Trivial data, so invest rigor in **stability analysis:** rolling 5-year returns of each window definition; heat-map of entry/exit day offsets — a real calendar effect shows a smooth ridge, an artifact shows a spike cell.
- Trade timezone/holiday calendars correctly (month boundaries differ across markets); international replication (10+ markets) is the anti-data-mining test [S1 did 34].
- For B: define the intra-month relative-return signal strictly ex-ante (through T−5 close); test the pressure leg and reversal leg separately — [S2]'s mechanism implies both legs profit; if only one does in your data, the mechanism read is wrong.
- Include 2015–2025 sample prominently (the live-question era); report vs an always-long benchmark for A (the timing claim must beat exposure-matched buy-and-hold).

## 8. Recommendations for use

- **Backtest priority: medium-high for effort-adjusted return** — days of work, institutional-grade question, and directly usable as *execution intelligence* even if never traded standalone: every strategy in the corpus that rebalances monthly should schedule its own trading *around* these windows (trade with the flow you'd otherwise pay).
- Deploy A/B as small overlays on the futures book if the post-2015 sample confirms; otherwise bank the execution-timing knowledge.
- Bundle conceptually with docs 07-02 (index flows) and 09-02 (roll congestion): one research theme — *predictable mechanical flow, priced*.
