# Macro-Announcement Drift (Pre-FOMC & Scheduled-Release Effects) — ⚠ flagged: headline effect decayed post-2015

## 1. Classification

- **Category:** Event-driven (macro calendar)
- **Asset classes:** Equity index futures (primary), rates futures, FX
- **Style:** Calendar-conditional directional exposure
- **Horizon:** Hours–2 days around scheduled announcements
- **Capacity:** Very high (index futures)
- **Complexity:** Low; **Data burden:** announcement calendar (FOMC, CPI, NFP with timestamps) + daily (ideally intraday) index futures

## 2. Economic rationale

Scheduled macro announcements resolve uncertainty at known times. Two documented patterns:

1. **Pre-FOMC announcement drift [E5]:** 1994–2011, the S&P earned ~49bp on average in the 24h *before* FOMC statements — ~80% of the total equity premium accrued in those ~8 days/year. Mechanism debate: compensation for holding equity into announcement risk (uncertainty-resolution premium) vs informal information leakage vs monetary-policy-expectation dynamics. **Kurov et al. [E6]: the drift disappeared after ~2015** (attributed to reduced policy uncertainty in the forward-guidance era, and, plausibly, publication).
2. **Announcement-day risk premia generally** (Savor & Wilson 2013): equity and bond returns concentrate on scheduled macro-announcement days (CPI/NFP/FOMC) — being paid for bearing announcement risk. This broader pattern has been more persistent than the specific pre-FOMC window.

Counterparty: investors who de-risk into announcements (paying to avoid event risk) and re-risk after. The economic core — *uncertainty-resolution premia exist at known calendar times* — is sound; the specific windows migrate as they get published and policy regimes change.

## 3. Signal & rules specification

Research program more than a fixed recipe (the honest framing given decay):

- **A. Announcement-day premium harvest:** long index futures from prior close to post-announcement close **only on scheduled announcement days** (FOMC, CPI, NFP), flat otherwise. The Savor-Wilson pattern: this captures a disproportionate share of the equity premium with ~30–40 exposure days/yr.
- **B. Pre-FOMC window (legacy):** long from 2pm the day before FOMC to the 2pm statement. Include as a *monitored* variant — expected ≈ 0 post-2015 [E6]; its value is as a decay-tracking series (it could return with higher policy uncertainty; 2022's hiking cycle showed flickers in some samples).
- **C. Post-announcement trend (rates/FX):** after big surprises (CPI beyond consensus by > 1σ), rates/FX drift in the surprise direction for 1–3 days (slow repricing of policy paths) — the macro cousin of PEAD. Signal: standardized surprise (actual − consensus)/σ(surprises); trade the direction in short-rate futures/FX for 1–3 days.
- **Sizing:** vol-scaled index/rates positions; these are overlay-scale allocations (≤ 5–10% of risk); costs negligible in futures.

## 4. Evidence & key research

- Lucca & Moench [E5]: the original — 49bp/24h pre-FOMC, 1994–2011, robust to controls, absent in other windows.
- Kurov, Wolfe & Gilbert [E6]: extension to 2019 — drift gone post-2015 in both press-conference and non-PC meetings.
- Savor & Wilson (2013, *JFQA*): announcement-day premia across decades — the broader, more durable pattern.
- Gürkaynak-Sack-Swanson and successors: high-frequency announcement-surprise responses in rates/FX — basis for variant C.
- **Decay status: B dead-or-dormant (post-publication + regime); A moderately persistent; C persistent but modest** (well-known, capacity-bound at short horizons — non-HFT sizing keeps you under the radar).

## 5. Expected performance profile

- A: captures 3–6%/yr of equity premium at ~15% of the calendar exposure — Sharpe of the *timing pattern* ~0.3–0.6 with huge per-day variance; best understood as an exposure-efficiency result.
- C: Sharpe **0.3–0.5** standalone at daily granularity; improves with intraday execution.
- Skew: announcement days carry two-sided jump risk — position sizes must respect single-print moves (CPI Oct-2022: ±5% intraday swings).
- Costs: minimal (index/rates futures).

## 6. Failure modes & risks

- **Regime dependence is the story:** these premia move with policy-uncertainty regimes; a strategy tuned to 1994–2011 lost its premise in 2015–2019. Continuous out-of-sample monitoring is part of the spec, not optional hygiene.
- Jump risk: the announcement *is* a scheduled gap; stops don't exist across a single print.
- Data pitfalls: announcement time changes across eras (FOMC statement times moved: 2:15 → 2:00 → press conferences), consensus-data vintages for C.
- Crowding at well-known windows (the decay mechanism itself).

## 7. Backtesting guidance

- Timestamp rigor: exact announcement datetimes per era (Fed's historical calendar; BLS release times); daily bars misalign the windows — intraday futures data strongly preferred for A/B, mandatory for C's short variants.
- Report **rolling 5-year windows** for every variant — the entire finding is regime-dependence [E6]; pooled full-sample averages are propaganda.
- For C: point-in-time consensus (survey vintages), surprise standardization on trailing windows only.
- Sample: 1994+ (FOMC-era structure); include 2022–2025 (revived macro-vol regime — the live question is whether premia revived with it).

## 8. Recommendations for use

- **Backtest priority: low-medium as alpha; medium as portfolio intelligence** — knowing that risk premia concentrate on announcement days should inform *every* strategy's risk management (e.g., vol-carry doc 06-01 already skips these days; equity sleeves can de-lever into CPI at no expected cost per variant A logic inverted).
- If traded: variant A as an exposure-timing overlay and C in rates futures at modest size; keep B as a monitored research series only.
- The announcement-calendar infrastructure built here feeds risk management corpus-wide — build it once regardless of whether this trades.
