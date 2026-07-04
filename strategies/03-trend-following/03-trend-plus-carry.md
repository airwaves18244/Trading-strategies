# Trend + Carry Combined (Signal-Level Integration)

## 1. Classification

- **Category:** Trend following × carry (composite; bridges categories 03 and 05)
- **Asset classes:** Futures/forwards multi-asset (FX, rates, commodities, equities); crypto perps
- **Style:** Directional per-market, diversified
- **Horizon:** Weeks–months; monthly/weekly rebalance
- **Capacity:** Very high
- **Complexity:** Medium; **Data burden:** trend inputs (doc 03/01) + carry inputs (futures curves, rate differentials — see category 05)

## 2. Economic rationale

Trend and carry are the two great futures risk premia, and they are **complementary by mechanism**: carry earns the *level* of the term-structure/yield gap (paid by hedgers and liquidity demanders for holding the unwanted side), trend earns the *change* (paid by slow reactors to regime shifts). Their return correlation is near zero to mildly negative; carry loses in exactly the crash regimes where trend wins (carry unwinds *are* trends). Combining at the **signal level** — one book netting both signals per market — rather than running two books:

1. cuts turnover (signals often offset → smaller trades),
2. avoids paying costs twice on opposing positions,
3. filters trend's worst whipsaws (a trend entry *against* rich carry is the lowest-quality trend trade: you pay negative carry while waiting; e.g., short a steeply backwardated commodity).

Counterparties: the union of both premia's payers. This doc exists separately because the *combination decision* (signal blend vs book blend, weights, conditional filters) is itself a documented research question with material P&L consequences.

## 3. Signal & rules specification

- **Universe:** the doc-01 futures universe (≥ 30 markets).
- **Trend signal** `T_i` ∈ [−1,1]: the doc-01 ensemble (1/3/12m or EWMA set).
- **Carry signal** `C_i` ∈ [−1,1]: annualized carry z-scored per market class:
  - Futures: `(F_near − F_far)/(F_far · Δτ)` (slope of curve = expected roll yield);
  - FX: short-rate differential vs USD (or forward discount);
  - Bonds: yield + rolldown − funding;
  - Crypto perps: funding rate.
  Cross-sectional or time-series z within asset class; clamp to [−1,1].
- **Combined:** `s_i = w_T·T_i + w_C·C_i` with w_T ∈ [0.5, 0.7] baseline (trend slightly overweighted for its crisis convexity); sensitivity-test 50/50.
- Alternative documented form — **carry-filtered trend:** take trend positions only when carry is not strongly opposed (|C| against T beyond a threshold → halve or skip). Simpler, similar effect.
- **Sizing/risk:** identical machinery to doc 01 (inverse-vol, class risk balance, 10–15% portfolio vol target, buffer rebalancing).

## 4. Evidence & key research

- Koijen et al. "Carry" [C1]: carry positive in all 9 asset classes tested; global diversified carry gross Sharpe ~1.1 (1983–2012); **carry and trend correlation ≈ 0** in their sample.
- AQR/Man Institute practitioner studies (e.g., "Carry and Trend in Lots of Places", Man AHL; AQR multi-strategy papers) [M-rated]: 50/50 trend+carry blends raise Sharpe ~30–50% over either alone and cut drawdowns; blend benefits robust across asset classes and decades.
- Kang, Rouwenhorst & Tang [T5]: both premia trace to hedging pressure — same payer, different moment of the term structure (level vs change), which is why they diversify without being unrelated.
- **Decay status:** inherits components' decay (trend modest; FX carry substantial post-GFC [C4], commodity/vol carry healthier). The *blend advantage* itself is structural (cost netting + negative co-crash), not a fragile anomaly.

## 5. Expected performance profile

- Net Sharpe: **0.6–0.9** diversified blend (vs 0.4–0.7 trend-only) — the most reliable Sharpe improvement documented in the futures literature.
- Skew: carry contributes negative skew, trend positive; blended book ≈ neutral skew with materially shallower drawdowns than either component.
- Turnover: *lower* than the sum of parts (netting); cost profile as doc 01.

## 6. Failure modes & risks

- **Correlation regime risk:** trend-carry correlation isn't guaranteed ≈ 0; in prolonged carry-friendly, trendless regimes both can chop; in a violent carry unwind trend needs time to flip (days–weeks of joint loss: e.g., Aug 2024 yen-carry unwind hit carry instantly while short-yen trend positions also lost).
- Carry measurement risk: curve-based carry embeds seasonality (gas winter contracts) — must use seasonally-aware slopes or same-month-next-year slopes for seasonal commodities, else "carry" is a seasonality artifact.
- Weight optimization temptation: w_T/w_C fitted per market on history will overfit; use one global weight.

## 7. Backtesting guidance

- Build ON TOP of validated doc-01 (trend) and category-05 (carry) backtests — never debug all three layers at once.
- The decisive reports: (a) Sharpe/DD of trend-only vs carry-only vs blend on identical universe/costs; (b) **turnover of blend vs sum of separates** (should drop 20–40% — if not, implementation isn't netting); (c) co-crash table: worst 20 carry weeks and trend's P&L in them.
- Seasonal-carry hygiene for commodities (same-tenor-next-year slope); FX carry from forwards (not raw policy rates — includes basis).
- Sample: 20y+; must include 2008 (carry crash + trend win), 2022 (both win), Aug-2024 (joint loss week).

## 8. Recommendations for use

- **Backtest priority: high** — but sequenced *after* trend and carry pass individually; it's the production form of the futures book (this is roughly what modern multi-strategy CTAs run).
- Recommended deployment: signal-level blend at 60/40 trend/carry weights, seasonally-corrected carry, one global weight set.
- Portfolio role: replaces separate trend and carry sleeves; budget its risk as "futures risk premia" ~25–40% of a diversified book.
