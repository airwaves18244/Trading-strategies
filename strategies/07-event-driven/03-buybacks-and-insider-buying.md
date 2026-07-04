# Buyback Announcements & Insider Buying (Informed-Insider Signals)

## 1. Classification

- **Category:** Event-driven (information signaling)
- **Asset classes:** Equities (US disclosure regime best; UK/EU/JP workable)
- **Style:** Long-tilted event portfolio, months-scale drift
- **Horizon:** Hold 3–12 months post-event
- **Capacity:** Medium
- **Complexity:** Low–medium; **Data burden:** buyback announcements (press releases/filings), insider transaction filings (Form 4 data), prices; all public-source

## 2. Economic rationale

Both events share one engine: **people with superior information about the firm putting money where their mouth is, and the market underreacting.**

- **Buybacks [E7]:** management announcing open-market repurchases signals perceived undervaluation (and mechanically shrinks share supply while adding a price-supportive bid). Underreaction: announcement pops ~2–3%, but abnormal returns of ~10–20% accumulate over the following 1–4 years, strongest for *value* stocks buying back after price declines — the "mispricing-correction" cohort.
- **Insider buying [E9]:** officers/directors buying their own stock with personal cash. Cohen-Malloy-Pomorski's key refinement: separate **opportunistic** buys (irregular timing — informative) from **routine** buys (same month yearly — noise); opportunistic buys predict large abnormal returns, clustered buys by multiple insiders more so.

Counterparty: sellers ignoring the highest-quality information signal available in public data. These decay slower than pure price anomalies because acting requires stock-level fundamental conviction and months of patience — arbitrage capital is structurally impatient.

## 3. Signal & rules specification

**A. Buyback cohort:**
- Event: announced open-market repurchase ≥ 5% of shares outstanding (bigger = stronger signal); actual-execution follow-through (from subsequent filings) upgrades the signal — announcements without execution are cheap talk.
- Condition on context: prior 6-month return negative or low valuation (B/M top half) — the documented strong cohort; skip buybacks by levered serial repurchasers at highs (financial-engineering cohort).
- Entry day +2 post-announcement; hold 6–12 months; overlapping cohorts; equal weight; 50–150 names.

**B. Insider cluster buys:**
- Event: ≥ 2 distinct insiders (esp. CEO/CFO) open-market buying within 30 days, aggregate value meaningful vs their comp (e.g., > $100k each); exclude routine-calendar buyers [E9] and option-related acquisitions (only open-market purchases count).
- Entry on filing publication date (+1); hold 3–6 months.
- **Combined A+B (buyback + insider buying same quarter):** the highest-conviction cohort — test as flagship variant.

- **Portfolio:** long-only tilt or hedged with index short; beta-hedge rather than short single names (no reliable negative signal on the short side — insider *selling* is mostly uninformative liquidity/diversification).
- **Sizing:** per-name ≤ 1.5%; book vol-targeted.

## 4. Evidence & key research

- Ikenberry, Lakonishok & Vermaelen [E7]: buyback announcers earn ~12% abnormal over 4 years (1980–90 sample); value-stock cohort ~45% cumulative; replicated internationally with smaller magnitudes.
- Peyer & Vermaelen (2009): effect persisted post-2000, concentrated in beaten-down announcers.
- Cohen, Malloy & Pomorski [E9]: opportunistic insider buys → ~7–10% annualized abnormal; routine buys → ~0. Cluster-buy refinements in subsequent literature strengthen it.
- Live-era: buyback-achievers indices outperformed through the 2010s; 2022–24 samples consistent (with buyback-tax noise); insider-cluster signals remain among the most robust public-data signals per replication studies.
- **Decay status: mild-moderate** — slower than price anomalies [X1]; both signals retain post-publication significance in recent samples, at reduced magnitude.

## 5. Expected performance profile

- Net (hedged): **3–8% annualized** on the tilt, Sharpe 0.4–0.7; long-only version: index + 2–4% with similar vol.
- Skew: positive-ish (occasional takeovers of buyback/insider-buy names — the information sometimes realizes via M&A).
- Turnover: low (multi-month holds); costs light (liquid enough universe, patient entries).

## 6. Failure modes & risks

- Value-trap cohort: insiders/management are optimists in secular decliners (energy 2014–19, banks 2007) — sector caps and diversification are the defense; the signal is *better information*, not *perfect information*.
- Signal gaming: announced-but-never-executed buybacks; insider buys staged for optics (small sizes) — the execution-follow-through and size filters address.
- Regime: long-tilted book underperforms in broad bear markets regardless of selection (hedge or accept).
- Regulatory drift: buyback taxation/rules (US 1% excise, potential changes) can alter announcement behavior over time.

## 7. Backtesting guidance

- Data: insider transactions are free-source (regulatory filings; parsed datasets available); buyback announcements from press-release/filing datasets — timestamp discipline (trade on public availability, day +1/+2).
- Event-study construction with overlapping cohorts (as PEAD doc); abnormal returns vs characteristic-matched benchmarks (size/value-matched), not just market — the cohorts are small-value-tilted, don't credit the factor to the event.
- Report by cohort: buyback size tercile, prior-return split, opportunistic-vs-routine insiders, cluster size; and the A+B intersection.
- Sample: 15y+; both signals have enough events (thousands) for statistical comfort.

## 8. Recommendations for use

- **Backtest priority: high among event strategies** — public data, slow decay, low costs, and genuinely differentiated information source; the natural second event project after the PEAD pipeline exists.
- Deploy as a long-tilted satellite (hedged to taste) with sector caps; the A+B intersection cohort concentrated at 20–40 names is the conviction version.
- Combines naturally with value/quality factor sleeves (shared data, complementary logic: factor says cheap, insiders say cheap *and they're buying*).
