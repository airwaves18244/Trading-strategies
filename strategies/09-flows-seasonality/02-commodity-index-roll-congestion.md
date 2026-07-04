# Commodity Index Roll Congestion (Front-Running the Goldman Roll) — ⚠ flagged: heavily decayed; case study + residual

## 1. Classification

- **Category:** Flows & seasonality (mechanical flow)
- **Asset classes:** Commodity futures (index-heavy markets: WTI, gas, ags)
- **Style:** Calendar-spread positioning around known roll windows
- **Horizon:** ~2-week windows monthly
- **Capacity:** Low–medium today
- **Complexity:** Medium; **Data burden:** futures chains + index roll-calendar rules (public)

## 2. Economic rationale

Commodity index products (GSCI/BCOM trackers — hundreds of billions at peak) roll futures on **published calendars** (canonically the 5th–9th business day monthly, the "Goldman roll"): selling the front, buying the next tenor, in size, price-insensitively. Anticipating this flow: buy the deferred / sell the front *before* the window (spread cheapens the front vs deferred as the roll flows through), unwind after. Mou [S3] documented double-digit annualized returns to front-running it in the 2000s — a pure structural-flow rent extracted from index investors (the cost showed up as index "roll drag"). **Why it decayed:** the trade was published and crowded; index providers introduced *flexible/enhanced roll* variants (spreading the roll across dates/tenors); index AUM growth flattened; by the mid-2010s the systematic pattern was mostly competed away. Included as (a) a rich case study in flow-edge lifecycle — the sharpest documented example, (b) a residual/episodic monitor: congestion still appears when index flows surge (2020–22 commodity inflow waves) or in smaller markets where the roll remains a large share of volume.

## 3. Signal & rules specification

- **Baseline (historical form):** ~5 business days before the index roll window: long 2nd/3rd-tenor contract, short front, in index-weighted markets; unwind across/after the window. Position = calendar spread (doc 01-06 machinery).
- **Modern conditional version (the testable residual):**
  - Track **roll pressure** per market: estimated index open interest as a share of front-contract OI/volume (CFTC index-trader/ CIT-type data, ETF AUM proxies);
  - Trade only markets/months where roll pressure exceeds a threshold (top quintile historically) — the mechanism needs enough flow to matter;
  - Signal validation per event: front-vs-second spread should cheapen abnormally in pre-roll days; require the pattern in trailing samples before deploying capital to a market.
- **Sizing:** small spread positions (≤ 0.3–0.5% risk per market-month); avoid delivery windows (doc 01-06 squeeze rules apply in full).

## 4. Evidence & key research

- Mou (2011) [S3]: front-running the GSCI roll 2000–2010 → 3.6%–24% annualized depending on aggressiveness; magnitude ∝ index AUM.
- Subsequent literature + index-provider changes (enhanced-roll indices, e.g., BCOM roll-select) document the response; post-2012 studies find the naive pattern's returns near zero — a textbook McLean-Pontiff arc [X1] in the flow domain.
- Kang-Rouwenhorst-Tang [T5] contextualizes: index flow is one of the hedging-pressure forces shaping tenor premia.
- **Decay status: the naive trade is dead; the monitored-conditional residual is a niche** — honesty requires stating most tests will conclude "no trade at current flow levels."

## 5. Expected performance profile

- Realistic modern expectation: **near-zero in normal regimes; episodic single-digit annualized in flow-surge windows** (2020–22-type) at small capacity.
- Skew: spread-trade profile; delivery/squeeze tails if rules ignored.
- Costs: spread executions are cheap; the constraint is edge size, not cost.

## 6. Failure modes & risks

- Trading the ghost: deploying to the pattern's 2000s parameters — the base-case error this doc exists to prevent.
- Roll-calendar changes (providers shift rules); CIT data lags and imprecision.
- Squeeze/delivery risk on the short front leg (2020 WTI applies — never carry into delivery).
- Small edges + episodic deployment = high ratio of infrastructure to P&L; opportunity cost is real.

## 7. Backtesting guidance

- Reconstruct the historical arc first (validation): your 2000–2010 backtest should reproduce Mou's magnitudes, then show the post-2012 decay — this *decay curve replication* is the pipeline test and the corpus's best empirical lesson in flow-edge lifecycles.
- Spread construction per doc 01-06 standards (contract-level data, settlements, roll rules explicit).
- Condition on flow proxies point-in-time (CFTC CIT supplemental data since 2007; ETF AUM series); report edge vs roll-pressure quintile — the residual claim lives or dies on that monotonicity.
- Include index-methodology change dates as regime breaks.

## 8. Recommendations for use

- **Backtest priority: low as capital deployment; medium as education** — bundle it into the commodity-infrastructure project (docs 01-06, 02-07, 05-02) as a one-week study.
- Keep as a *monitored playbook*: an alert on roll-pressure metrics; deploy only when the conditional evidence re-emerges.
- The general lesson feeds the whole flows category: mechanical-flow edges are real, datable, and mortal — build the monitoring, not the faith.
