# Trading Strategies — Research Corpus & Backtest Terminal

## qbt — the backtest terminal

All 43 documented strategies are implemented as parameterized, modifiable code in
[`qbt/strategies/`](qbt/strategies/) (one file each, auto-registered), backed by a
vectorized weights engine + an order engine with stops/targets, realistic cost
models, a look-ahead validation harness, and a local web terminal: equity vs
benchmark with drawdown band, monthly-returns heatmap, rolling Sharpe/vol/beta,
alpha/beta/IR vs MCFTR, per-symbol P&L attribution, trade stats, top-drawdown
table, parameter sweeps with an in-sample/out-of-sample Sharpe split, and
side-by-side comparison of saved runs (dark/light theme, keyboard-driven).

**The terminal runs locally on your own machine** — it is a local web app, not a hosted
service. Clone the repo, install, pull data, then open `http://127.0.0.1:8000` in the
browser *on that same machine*.

```bash
git clone -b claude/trading-strategies-research-qhrq6q \
    https://github.com/airwaves18244/Trading-strategies.git
cd Trading-strategies

python -m venv .venv
.venv\Scripts\activate        # Windows  (macOS/Linux: source .venv/bin/activate)

pip install -e ".[dev]"
copy .env.example .env        # add QBT_FINAM_SECRET / QBT_ALGOPACK_TOKEN (optional)

qbt serve --fake              # try the UI instantly on a canned engine
qbt data ensure --universe moex_liquid --start 2015-01-01   # pull free MOEX ISS history
qbt data ensure --universe forts_core --start 2015-01-01
qbt serve                     # real engine at http://127.0.0.1:8000

qbt run ts_momentum -p per_asset_target=0.15 --start 2018-01-01   # CLI backtest
qbt sweep breakout_channel -p channel=20:100:10                    # parameter sweep
qbt new-strategy my_idea      # scaffold strategy #44
```

Data sources: **MOEX ISS** (free, no key — bars, PIT index membership, dividends,
futures chains), **Finam Trade API** and **MOEX ALGOPACK** (your keys via `.env`;
endpoints marked VERIFY-ON-WINDOWS need `qbt dev record-fixtures` on your machine),
plus CSV/parquet import for event data (`qbt/data/schemas.py` documents the 14
schemas — deals, earnings, funding rates, vol curves…; drop files into `data/events/`).

Strategy groups: **A** (26) run on MOEX data out of the box; **B** (13) need a CSV
event schema and ship with synthetic fixtures so they run green immediately;
**C** (4) are data-gated research implementations. Architecture, workstream map and
risk decisions: [`docs/architecture.md`](docs/architecture.md). Tests: `pytest` —
103 checks including a registry-wide look-ahead harness and cost-monotonicity on
every strategy.

---

## The research corpus

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
