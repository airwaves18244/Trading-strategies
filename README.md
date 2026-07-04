# Trading Strategies — Research Corpus

Research on **43 non-HFT trading strategies** across 10 categories, built as the foundation for a subsequent backtesting program. Every strategy included has a real economic rationale (risk premium, behavioral effect, structural flow, or market friction) — strategies defined purely by technical-indicator mechanics were excluded by design.

Produced following the `flows/universal.md` research flow from [airwaves18244/REASERCH-PLAN](https://github.com/airwaves18244/REASERCH-PLAN): Scoping → Landscape scan → Deep investigation → Synthesis → Critique → Report.

## How to navigate

- **[SUMMARY.md](SUMMARY.md)** — start here. What was investigated, master comparison table, cross-cutting insights, recommended backtesting order.
- **`strategies/`** — one document per strategy, grouped by category:

| Folder | Category | Docs |
|--------|----------|------|
| `01-arbitrage-relative-value/` | Arbitrage & relative value | 7 |
| `02-momentum/` | Momentum (cross-sectional & time-series) | 7 |
| `03-trend-following/` | Trend following | 3 |
| `04-mean-reversion-swing/` | Mean reversion & swing | 4 |
| `05-carry/` | Carry | 5 |
| `06-volatility/` | Volatility | 4 |
| `07-event-driven/` | Event-driven | 5 |
| `08-value-fundamental-factor/` | Value & fundamental factors | 3 |
| `09-flows-seasonality/` | Flows & seasonality | 3 |
| `10-crypto-specific/` | Crypto market structure | 2 |

- **`research/`** — flow artifacts: `00-brief.md` (scope & success criteria), `01-landscape.md` (source log with credibility ratings), `04-critique.md` (red-team pass over the whole set).

## Per-strategy document structure

Every strategy document follows the same 8 sections, so they can be compared and handed to a backtesting pipeline directly:

1. **Classification** — asset classes, style, horizon, capacity, complexity, data burden
2. **Economic rationale** — why the edge exists and who is on the other side
3. **Signal & rules specification** — universe, data, signal math, entry/exit, sizing, rebalancing, parameter ranges
4. **Evidence & key research** — sources with reported results and post-publication decay status
5. **Expected performance profile** — realistic Sharpe range, skew, turnover, cost sensitivity
6. **Failure modes & risks** — losing regimes, crowding, historical blow-ups
7. **Backtesting guidance** — pitfalls, minimum data, test design, cost assumptions
8. **Recommendations for use** — standalone viability, portfolio role, backtest priority

## Status

Research complete. Next stage: backtesting (out of scope for this repo — see SUMMARY.md for the prioritized order).
