# UI upgrade v2 — frozen contract

Goal: bring the terminal to commercial-backtester quality (TradingView Strategy
Tester / Portfolio Visualizer / Amibroker class) while staying a pragmatic local
app. Four parallel workstreams with **disjoint file ownership**; everything they
share is frozen in this document. If something here is ambiguous, the section
owner decides for their own files and documents the decision in a code comment —
do NOT edit another workstream's files.

| WS | Owns | Does NOT touch |
|----|------|----------------|
| A  | `qbt/analytics/report.py` (new), `qbt/analytics/drawdown.py`, `qbt/analytics/attribution.py`, `qbt/engine/result.py`, `qbt/engine/sweep.py`, `tests/analytics/test_report.py` (new) | api/, web/ |
| B  | `qbt/api/app.py`, `qbt/api/schemas.py`, `qbt/api/jobs.py`, `qbt/api/fake.py`, `tests/api/test_app.py` | analytics/, engine/, web/ |
| C  | `qbt/web/static/charts.js` | everything else |
| D  | `qbt/web/templates/index.html`, `qbt/web/static/app.js`, `qbt/web/static/styles.css` | charts.js, api/, analytics/ |

No new vendor libraries: ECharts + Alpine only (already in `static/vendor/`).
Nobody commits to git — the integrator commits.

---

## 1. run.json v2 (WS-A produces, C/D consume)

`BacktestResult.to_run_json()` keeps every existing key unchanged
(`meta, metrics, equity, equity_gross, drawdown, benchmark, exposure, per_year,
costs_total, trades, n_trades`) and **adds** the keys below. Every new key is
ALWAYS present — `null` / `[]` when not applicable. Time is unix seconds, dates
are `"YYYY-MM-DD"` strings, returns/fractions are decimals (0.12 = 12%).

```jsonc
{
  "exposure": { "...existing...": [], "n_positions": [{"time":0,"value":0}] }, // n_positions ADDED to the dict

  "benchmark_stats": {          // null when benchmark_equity is None
    "symbol": "MOEX:MCFTR",     // = benchmark_equity.name if truthy else "benchmark"
    "sharpe": 0.0, "cagr": 0.0, "ann_vol": 0.0, "max_dd": 0.0,   // of the benchmark itself
    "alpha_ann": 0.0,           // (mean(r) - beta*mean(rb)) * 252, from daily net vs bench returns
    "beta": 0.0,                // cov(r, rb) / var(rb)
    "corr": 0.0,
    "te_ann": 0.0,              // std(r - rb) * sqrt(252)
    "ir": 0.0                   // mean(r - rb) / std(r - rb) * sqrt(252)
  },

  "monthly": {                  // calendar net returns; compounded within month
    "years": [2018, 2019],
    "cells": [[0.01, null, ...12 entries...], ...],   // null = no data that month
    "totals": [0.12, -0.05]     // compounded per-year total (same row order)
  },

  "drawdowns": [                // top 10 by depth, deepest first (reuse analytics.drawdown.drawdown_periods)
    {"start": "2020-02-20", "trough": "2020-03-18", "end": "2020-11-05",  // end null if not recovered
     "depth": -0.35, "days": 180, "recovery_days": 160}                   // recovery_days null if not recovered
  ],

  "rolling": {                  // 252-bar window over net returns; first 251 points skipped (not null-padded)
    "ts": [1500000000],         // downsampled together to <= 1500 points
    "sharpe": [0.5], "vol": [0.2],
    "beta": [0.9]               // null (the whole key) when no benchmark
  },

  "attribution": [              // per-symbol P&L contribution, sorted by pnl desc, max 50 rows
    {"symbol": "MOEX:SBER", "pnl": 0.15,        // cumulative contribution to NAV (fraction)
     "avg_weight": 0.04, "n_trades": 12}        // n_trades 0 for weight-engine runs is fine
  ],

  "trade_stats": {              // null when trades ledger has no rows with non-null pnl
    "n": 120, "win_rate": 0.55, "profit_factor": 1.4,
    "avg_win": 0.01, "avg_loss": -0.007, "expectancy": 0.002,
    "avg_hold_days": 12.5,      // null if entry/exit pairing unavailable
    "best": 0.05, "worst": -0.04
  }
}
```

Implementation home: `qbt/analytics/report.py` exposes pure functions
(`monthly_table(returns)`, `rolling_stats(returns, bench_returns)`,
`benchmark_stats(returns, bench_equity, symbol)`, `trade_stats(trades)`,
`attribution_rows(weights, returns | positions, trades)`) and
`extend_run_json(result, out: dict) -> dict` that mutates/returns the payload.
`to_run_json` calls `extend_run_json`. FakeRunner and RealRunner both return
`BacktestResult`, so both engines get v2 for free — WS-B must not special-case.

### Sweep IS/OOS (WS-A, `qbt/engine/sweep.py`)

Each sweep row gains `sharpe_is` and `sharpe_oos`: split net daily returns at
70% of observations (first 70% = IS, last 30% = OOS), Sharpe on each side.
Existing columns unchanged. WS-B mirrors the two columns in the fake sweep.

---

## 2. API v2 (WS-B produces, D consumes)

Existing endpoints keep their shapes except where extended below.

```
GET  /api/runs
  → rows now include (merged into status.json by jobs.py):
    strategy_key, universe, start, end, params (dict),
    label (str, default ""), starred (bool, default false),
    summary: {"sharpe": f, "cagr": f, "max_dd": f} | null   // null until done; filled on completion for kind=="backtest"

PATCH  /api/runs/{run_id}      body {"label"?: str, "starred"?: bool}
  → 200 updated status row; 404 unknown

DELETE /api/runs/{run_id}
  → {"ok": true}; removes runs/<id> dir + registry entry; 409 if state=="running"|"queued"

GET  /api/compare?ids=a,b,c    (2..6 ids)
  → {"runs": [{"run_id", "label", "meta": {...RunMeta...}, "metrics": {...},
               "equity": [{"time","value"}]}]}              // net equity, downsampled ≤1500 pts
  → 404 listing missing ids; only state=="done" backtest runs allowed (400 otherwise)

POST /api/runs — submit meta now stores strategy_key/universe/start/end/params
                 (jobs.submit(meta=...)); on completion jobs.py computes summary
                 from the BacktestResult metrics (sharpe, cagr, max_dd).
```

`jobs.py` additions: `patch(run_id, **fields)`, `delete(run_id)` (raises
RunningJobError → app maps to 409), completion hook writes `summary`. Label and
starred persist in `status.json`. FakeRunner: sweep rows get plausible
`sharpe_is`/`sharpe_oos` (e.g. sharpe ± noise) so the UI is developable offline.

---

## 3. QCH chart API (WS-C produces, D consumes)

`charts.js` defines global `QCH`. All charts render into `#chart-main`,
one ECharts instance reused, `QCH.dispose()` clears it. **All colors come from
CSS custom properties** (section 4) via
`getComputedStyle(document.documentElement).getPropertyValue(...)` read at call
time (theme can flip between calls; re-render on toggle is D's job).

```js
QCH.equity(result, opts)   // opts: {log?: bool, gross?: bool}
   // net line + optional gross dashed + benchmark line (if result.benchmark)
   // + drawdown as a dim red area band on a secondary right axis
   // log: y axis type 'log'
QCH.drawdown(result)       // underwater area; top-5 result.drawdowns shaded with markArea + depth labels
QCH.monthly(result)        // heatmap year rows × 12 month cols + a separated "YEAR" total column,
                           // diverging palette --neg → --panel → --pos, cell labels in --text
QCH.rolling(result, which) // which in "sharpe"|"vol"|"beta"; zero-line marked; vol shown in %
QCH.exposure(result)       // gross/net/long/short lines (short negative), n_positions on right axis
QCH.candles(bars, trades, symbol)
   // candlestick + volume sub-grid; trades → entry/exit arrows (side>0 up-triangle --pos below bar,
   // side<0 down-triangle --neg above bar), tooltip shows qty/price/pnl/reason
QCH.heatmap(rows, p1, p2OrNull, metric)
   // metric in {"sharpe","sharpe_is","sharpe_oos","cagr","max_dd","turnover_ann"}
   // p2 null → line chart of metric vs p1 with point labels instead of a 1-row heatmap
QCH.compare(items)         // items: [{label, equity: [{time,value}]}]
   // each series normalized to 1.0 at its first point; legend = labels; distinct colors from --s1..--s6
QCH.dispose()
```

Charts must survive `null` metric values and empty arrays without throwing.
Number formatting inside charts: percents 1 decimal, ratios 2 decimals.

---

## 4. Theme variables (WS-D defines in styles.css, C reads)

Dark is the default; light theme via `body.light`. D owns the toggle + persistence.
Both themes MUST define all of:

```
--bg        page background          --panel   card/tooltip background
--panel2    inset background         --border  hairline borders
--text      primary text            --muted   secondary text
--accent    primary interactive     --pos     gains (green family)
--neg       losses (red family)     --warn    warnings (amber)
--bench     benchmark series        --grid    chart gridlines
--s1..--s6  categorical series palette (compare mode, exposure lines)
```

## 5. Shell spec (WS-D)

* Layout stays 3-pane (strategies | chart | results), header gains a slim global
  progress bar and a theme toggle. Panels get min-widths + the page never
  scrolls horizontally.
* Center tabs: `Equity · Drawdown · Monthly · Rolling · Exposure · Chart · Sweep · Compare`.
  Equity tab has `log` and `gross` checkbox toggles; Rolling has a
  sharpe/vol/beta switch; Sweep has a metric select (incl. `sharpe_oos`);
  Chart tab gets a symbol select (populated from result attribution or universe).
* Right tabs: `Summary · Years · Trades · Attribution · Costs · Doc · Data`.
  - Summary: metrics grouped under `returns / risk / trading` headings + a
    `vs benchmark` block from `benchmark_stats` (alpha, beta, IR, corr, TE).
  - Trades: header chips from `trade_stats` (win rate, PF, expectancy…), table
    below (existing), CSV export stays.
  - Attribution: table from `attribution` (symbol, pnl %, avg weight, trades),
    positive/negative pnl marks.
* History rows: sharpe chip (colored by sign) from `summary`, star toggle,
  delete ×, checkbox for compare (2–6, then a COMPARE button appears), label
  set via pencil/dblclick → PATCH. Tooltip shows params JSON.
* Keyboard: `Ctrl/Cmd+Enter` run, `/` focus search, `Esc` dismiss error.
* Persistence: `localStorage` for form values, selected strategy, theme, last
  active tabs. Restore on load.
* Formatting rules (match `fmt/pct/num`): percents 1 decimal, ratios 2, counts
  integer, em-dash for null.

## 6. Definition of done (all WS)

* `pytest` green from repo root (A and B add/extend tests; C and D cannot break collection).
* No console errors with the FAKE runner across every tab (integrator verifies with Playwright).
* Existing CLI (`qbt run/sweep/serve`) untouched.
