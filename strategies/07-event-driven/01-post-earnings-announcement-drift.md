# Post-Earnings Announcement Drift (PEAD)

## 1. Classification

- **Category:** Event-driven (information-diffusion anomaly)
- **Asset classes:** Equities (global; strongest evidence US historically, now better ex-US/small-cap)
- **Style:** Cross-sectional event portfolio, long-short
- **Horizon:** Entry ~1 day post-announcement; hold 2 weeks–3 months (to next announcement)
- **Capacity:** Low–medium (edge lives where liquidity is thin)
- **Complexity:** Medium; **Data burden:** point-in-time earnings (actuals + analyst consensus with timestamps) + prices — the data is the project

## 2. Economic rationale

Stocks beating earnings expectations continue drifting up for weeks–months after the announcement (and misses drift down). Mechanism: **underreaction to earnings news** — investors anchor on old earnings levels, under-appreciate the *autocorrelation of earnings surprises* (a beat this quarter predicts a beat next quarter — Bernard-Thomas's core finding), and information processing is limited (small firms, few analysts, low attention → bigger drift). Counterparty: inattentive holders slow to update, and disposition-effect sellers into good news. It is the cleanest behavioral-underreaction anomaly ever documented — and precisely for that reason, among the most arbitraged in liquid US large caps [E2].

## 3. Signal & rules specification

- **Surprise measure (test all three; they overlap ~70%):**
  1. **SUE:** (actual EPS − expected) / σ(surprises), with expected from analyst consensus (point-in-time snapshot immediately pre-announcement) or seasonal-random-walk (EPS_q − EPS_{q−4}) where consensus is thin;
  2. **Announcement return (CAR3):** market-adjusted return over days [−1,+1] — the market's own verdict, no consensus data needed, robust to earnings-quality games;
  3. Combined: require agreement (SUE > 0 AND CAR3 > 0) — the strongest drift per unit of position.
- **Universe:** all listed above liquidity floor; **the effect concentrates in small/mid caps and low-analyst-coverage names** — the universe choice trades edge vs costs explicitly.
- **Portfolio:** event-time construction — enter day +2 after announcement (skip the chaotic +1), long top surprise quintile / short bottom; hold 60 trading days or until next announcement; overlapping event cohorts, continuously rebalanced.
- **Sizing:** equal-weight within cohort, per-name cap 1%; book beta-hedged (index futures) — PEAD itself is ~market-neutral by construction but cohorts can tilt.
- **Refinements with evidence:** stronger after-hours announcements drift from next open (define event time by timestamp); drift stronger when surprise contradicts recent price trend (genuine news); avoid names with concurrent M&A/guidance chaos.

## 4. Evidence & key research

- Bernard & Thomas (1989/90) [E1]: ~18% annualized hedge-portfolio abnormal return historical; drift explained by surprise autocorrelation ("the market misses that beats repeat").
- Fink (2021) survey [E2]: effect replicated across 50 years and many markets; **US large-cap magnitude now near insignificance**; persists in small caps, low-coverage stocks, and several non-US markets.
- Columbia/CEASA [E3]: decline attributed partly to falling earnings-news persistence (structural, not just arbitrage).
- Trading-frictions work (2024) [E2-adjacent]: initial reactions weakened but drift per unit friction stable — the surviving edge is a *frictions rent*.
- **Decay status: heavy in liquid US; alive in the illiquid/inattentive corners — which is a cost problem by definition.**

## 5. Expected performance profile

- Net Sharpe: **0.2–0.4** in a realistic liquid-universe implementation; **0.4–0.7** in small/mid-cap versions *if* cost modeling is honest (many are not).
- Skew: mild; event diversification (hundreds of announcements/quarter) smooths the book.
- Turnover: high (event-driven churn); cost sensitivity: **decisive**, same class as short-term reversal.
- Seasonal cadence: P&L concentrates in the four earnings seasons.

## 6. Failure modes & risks

- Costs eating the edge (the base case in large caps — assume it until your backtest proves otherwise).
- Consensus-data quality: stale or retroactively-revised estimates fabricate surprises (point-in-time snapshots are non-negotiable).
- Regime risk: macro-dominated tapes (2008, 2020, 2022) drown single-name earnings signals; drift weakens when correlation spikes.
- Short-leg frictions in small caps (borrow scarce exactly where the negative drift lives) — many live books run long-tilted.

## 7. Backtesting guidance

- **Point-in-time discipline is the whole game:** announcement timestamps (before/after market), consensus snapshots frozen pre-announcement, actuals as-reported (not restated). IBES-style data with snapshot history, or build forward from a live collection date.
- Event-study methodology: abnormal returns vs market/industry; entry day +2; report the drift *curve* (CAR by event day 0–90) — its shape (front-loaded, decaying) validates against the literature.
- Delisting/survivorship handling as always; the short leg's small-cap borrow costs modeled explicitly (or run long-only variant honestly).
- Report by cap tercile, coverage tercile, decade, and SUE-vs-CAR3 signal choice — the decision output is *which pocket, if any, clears your costs*.
- Sample: 15y+ with full point-in-time earnings data (the binding acquisition).

## 8. Recommendations for use

- **Backtest priority: medium** — gated on earnings-data acquisition; high knowledge value (the event-study pipeline generalizes to every event strategy in this category).
- Realistic deployment for an independent quant: long-tilted small/mid-cap PEAD as a seasonal sleeve, or CAR3-based (no consensus data needed) as the budget version.
- If the backtest shows large-cap US net alpha, distrust the cost model before trusting the alpha.
