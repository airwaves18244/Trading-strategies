# Fundamental Seasonality (Commodity Seasonals, Dividend Months, Calendar Effects with Causes)

## 1. Classification

- **Category:** Flows & seasonality (recurring-cause calendar patterns)
- **Asset classes:** Commodities (physical seasonals), equities (dividend-month, Halloween/turn-of-year), cross-market
- **Style:** Calendar-conditional positioning
- **Horizon:** Weeks–months, annually recurring
- **Capacity:** Medium
- **Complexity:** Low–medium; **Data burden:** long daily/monthly histories (seasonality needs many annual cycles); dividend calendars for the equity variant

## 2. Economic rationale

Seasonality is admissible under this corpus's rules **only where a physical or institutional cause exists** — otherwise it's the archetype of data-mined noise (52 weekly patterns × hundreds of assets = guaranteed spurious hits). The defensible set:

1. **Commodity physical seasonals:** demand/supply cycles are real — natural-gas heating demand, gasoline driving season, harvest supply gluts in grains. Prices *partially* embed them (the futures curve prices known seasonality — the tradable question is whether *risk premia*, not price levels, vary seasonally: e.g., pre-winter gas holds a scarcity-risk premium; pre-harvest grains carry weather-risk premia that decay post-harvest). Trade the *spread/premium seasonality*, not the naive "gas rises in winter" (it doesn't — the curve already knows).
2. **Dividend-month premium [S6]:** stocks earn abnormal returns in their predicted dividend months (price pressure from dividend-seeking flows + no risk story) — a within-stock calendar flow effect.
3. **Cross-sectional return seasonality [S5]:** stocks' relative performance in a given calendar month repeats (same-month winners over past years outperform this year) — attributed to recurring flow/attention patterns (fiscal years, window dressing, tax cycles).
4. **Halloween/turn-of-year [S4]:** documented across 65 markets/centuries (Halloween) but cause remains speculative (vacation/attention cycles) — include only as a *conditioning tilt*, weakest-confidence member, US effect weak post-publication.

Counterparties: calendar-locked physical hedgers, dividend-capture and tax-motivated flows, fiscal-year institutional rhythms.

## 3. Signal & rules specification

- **A. Commodity seasonal risk premia:** per market, compute average excess return (roll-adjusted, per corpus standards) by calendar month over ≥ 15 years, with block-bootstrap significance; trade only months with (i) significance surviving multiplicity correction, (ii) a nameable physical cause, (iii) out-of-sample confirmation in a holdout decade. Expressions: outright with tight risk, or better, the seasonal *calendar spreads* of doc 01-06 §Signal-3 (winter/summer NG, old-crop/new-crop) where the cause maps to specific tenors.
- **B. Dividend-month [S6]:** long stocks in months when they're predicted to pay (predicted from 12-months-ago payment calendar), short non-payers matched on characteristics; monthly rebalance. Modest but clean.
- **C. Heston-Sadka cross-sectional [S5]:** rank stocks by their average same-calendar-month return over past 5–20 years; long top / short bottom decile monthly. Combine with standard momentum controls (the signal must add beyond it).
- **D. Halloween tilt [S4]:** Nov–Apr overweight / May–Oct underweight equity beta as a *scaling* input (±20–30% exposure), never a binary in/out.
- **Sizing:** each is a small sleeve/tilt (≤ 5% risk each); A concentrated in 2–4 best-evidenced market-months.

## 4. Evidence & key research

- Heston & Sadka [S5]: same-month cross-sectional persistence up to 20 years back; survives momentum controls in-sample.
- Hartzmark & Solomon [S6]: dividend-month abnormal returns ~50bp/month with price-pressure mechanics (and reversal after).
- Bouman & Jacobsen [S4] + updates: Halloween across 65 markets, 300+ years in the UK; but US post-1998 out-of-sample weak; mechanism unresolved.
- Commodity seasonal premia: scattered but consistent evidence in energy/ags term-structure studies ([C5][C6] framework); practitioner seasonal-spread trading has a long commercial history.
- **Decay status: B/C moderately fresh with modest magnitudes; A persistent where physical (weather risk can't be arbitraged away, only priced); D weakest.**

## 5. Expected performance profile

- Realistic aggregate: **1–3%/yr portfolio contribution** from the combined sleeves at small risk; Sharpe per sleeve 0.2–0.4 — this category is seasoning, not the meal.
- Skew: A carries weather-tail risk (short-premium months can explode: Feb-2021 Texas freeze); B/C near-symmetric; D inherits equity skew.
- Costs: low (monthly, liquid instruments); C's turnover is the highest (full monthly re-rank).

## 6. Failure modes & risks

- **Multiplicity mirage:** the category's defining risk — seasonal patterns are where backtest overfitting goes to breed [X3]; the three-condition rule in §3A is the spec, not advice.
- Climate/structural drift: warming winters, shale, EV adoption shift physical seasonals over decades — anchor causes, re-verify periodically.
- Crowding on famous seasonals (January effect died decades ago — the historical warning).
- Weather tails on premium-selling months.

## 7. Backtesting guidance

- **Multiplicity correction is mandatory:** with 12 months × N assets, use Bonferroni/FDR or block-bootstrap null distributions; report how many "significant" patterns survive (expect: few).
- Split-sample discipline: patterns selected on 1990–2010 must confirm on 2011–2025 untouched.
- A: seasonal analysis on *excess* (roll-adjusted) returns only — spot seasonality that the curve already prices is untradeable (§2); the deseasonalized-carry cross-check with doc 05-02 catches double counting.
- B: point-in-time dividend calendars; C: replicate Heston-Sadka's momentum-controlled result before trusting extensions.
- Long histories: ≥ 20 annual cycles for any pattern claimed.

## 8. Recommendations for use

- **Backtest priority: low-medium** — after the core futures/equity pipelines exist, A and B are quick add-ons; C is a fuller project.
- Deploy only pattern-by-pattern with causes named in writing; cap the category's total risk; treat D as an exposure-scaling input at most.
- The category's meta-value: its methodology (multiplicity-corrected calendar analysis) is the immune system you'll reuse to *reject* the endless seasonal patterns the backtesting phase will surface.
