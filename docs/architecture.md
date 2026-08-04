# qbt — Architecture & Workstream Contract

Design: opus Plan agent; amended by Fable 5 review (all REQUIRED changes incorporated).
**PHASE 0 contract files are frozen** — change only via WS-F integration:
`qbt/core/types.py`, `qbt/core/errors.py`, `qbt/data/interfaces.py`, `qbt/data/schemas.py`,
`qbt/engine/context.py`, `qbt/engine/costs.py`, `qbt/engine/result.py`,
`qbt/strategy/base.py`, `qbt/strategy/registry.py`, `qbt/testing/synthetic.py` (signatures),
`tests/conftest.py`, `pyproject.toml`.

## Product

Local backtesting terminal (Windows target) for the 43-strategy research corpus in `strategies/**.md`.
Data: MOEX ISS (free), Finam Trade API (user's key), MOEX ALGOPACK (user's key), CSV/parquet import.
UI: FastAPI + Jinja2 + Alpine.js + **ECharts only** (vendored; candles, equity, drawdown, heatmap — one chart lib per review). CLI via typer. No auth, no live trading, no streaming, no Docker, no i18n — see "OUT of MVP" below.

## Package layout & ownership

| Path | Owner | Notes |
|------|-------|-------|
| `qbt/core/{config,calendar,ratelimit}.py` | **WS-A** | pydantic-settings (.env, QBT_ prefix); MOEX calendar incl. Feb–Mar-2022 halt; token bucket |
| `qbt/data/{store,manifest,service,adjust,futures,universe}.py` | **WS-A** | ParquetBarStore (`cache/bars/freq=<f>/symbol=<SYM>/data.parquet`, raw only), sqlite manifest (WAL, per-thread conns), incremental `DataService.ensure()`, read-time div adjustment → TR series, continuous futures (`RollRule(method=oi|volume|days_before_expiry, adjustment=difference|ratio|none)`, `ContinuousSeries(price, ret, held)`), Universe impls: Static, Index (PIT via ISS analytics), Liquidity (defer if tight) |
| `qbt/data/providers/**` | **WS-B** | `moex_iss.py` (bars, PIT universe by date, dividends, FORTS chains `show_expired=1`, filter calendar-spread secids `len(secid)!=4`→drop), `algopack.py` (supercandles, tradestats/obstats for spread calibration; **200-with-HTML-login ⇒ ProviderAuthError**, check content-type), `finam.py` (REST only: secret→JWT 15-min refresh w/ 2-min margin, `SBER@MISX` mapping, 200/min bucket), `files.py` (CSV/parquet import incl. event schemas via `qbt.data.schemas.validate_events`), `__init__.py` registry by name |
| `scripts/record_fixtures.py`, `configs/providers.example.yaml`, `configs/instruments/moex_aliases.yaml`, `tests/providers/**`, `tests/fixtures/**` | **WS-B** | ISS cassettes recordable from this container (`--provider moex_iss`, mark tests `network` for recording only); Finam/ALGOPACK cassettes hand-written from docs, tests marked `contract` |
| `qbt/engine/{weights,orders,portfolio,risk,runner,sweep}.py`, `qbt/engine/cost_models.py`, `qbt/analytics/**`, `qbt/testing/synthetic.py` bodies, `configs/costs/*.yaml`, `tests/engine/**`, `tests/analytics/**` | **WS-C** | see Engine spec |
| `qbt/strategy/lib/**` (family engines), `tests/strategy_lib/**` | **WS-D1** | see Family engines |
| `qbt/strategies/*.py` for D2 set, `tests/strategies/test_d2_*.py`, `configs/universes/*.yaml` | **WS-D2** | equity cross-sectional + event strategies (18 files, table below) |
| `qbt/strategies/*.py` for D3 set, `tests/strategies/test_d3_*.py`, `configs/runs/*.yaml` | **WS-D3** | futures/TS/carry/vol/crypto (25 files) |
| `qbt/api/**`, `qbt/web/**`, `qbt/cli.py`, `tests/api/**` | **WS-E** | FastAPI app, job registry (ThreadPoolExecutor, single-worker, no `--reload`; runs under `runs/<run_id>/`), UI, CLI (`qbt data ensure`, `qbt run`, `qbt sweep`, `qbt new-strategy`, `qbt dev record-fixtures`) |
| `docs/**`, integration | **WS-F** | only WS allowed to cross ownership; runs last |

Rules for every workstream: Python 3.11, `pathlib` everywhere (Windows target), UTC tz-aware timestamps, no network in tests (autouse socket block; use `network`/`contract` marks), all bars pass `BarFrame.validate`, do not edit files outside your ownership, add deps only if already in pyproject.

## Engine spec (WS-C)

- **WeightEngine** (vectorized): `pnl_t = w_{t-1}·r_t − costs_t`; input = weights matrix post-overlay; applies `shift_for_execution(lag)` (single choke point, default 1), risk pipeline (`ex_ante_vol` EWMA hl=20 strictly lagged → `inverse_vol_weights` → `vol_target(target, cap=2.0, floor=0.3, band=0.15)` → `apply_caps(per_instrument, gross, group)`), cost model, delisting returns from ctx.
- **OrderEngine** (bar loop): resolves `OrderIntent.size_mode` (`risk_frac` = NAV·size/|entry−stop|; `nav_frac`; `target_weight`; `qty`) against runtime NAV; conservative fills: gap-through-stop fills at next open; stop&take both inside one bar ⇒ stop first; time_stop_bars; trades ledger with per-trade pnl.
- **Normalization**: both engines emit full `BacktestResult`; for order strategies `weights` = realized position notional/NAV so exposure/turnover are comparable.
- **Overlay** applied by runner between generate() and execution lag; runner warns overlay+orders-strategy and overlay on strategies with `compatible_overlays=()`.
- **cost_models.py**: `FlatCostModel`, `SqrtImpactCostModel` (default; commission+fees+half-spread+impact_coef·(traded/ADV)^0.5, borrow on shorts), `AlgopackSpreadCostModel` (per-instrument spread frame).
- **analytics/metrics.py** `summary()`: sharpe, sortino, cagr, ann_vol, max_dd, dd_duration_days, calmar, skew, kurtosis, hit_rate, turnover_ann, avg_gross/net exposure, cost_drag_bps_ann, t_stat, best/worst year. `per_year_table` **must include a split row at 2022-02-24** (regime split first-class). `episode_table(trades)` for episodic strategies. `attribution.py`: gross vs net vs cost components.
- **validation.py**: `assert_no_lookahead(strategy, ctx, cut_dates≥3, incl. episode boundary)` — `generate(full)[:t]` must equal `generate(ctx.slice(t))`; `cost_sensitivity(strategy, ctx, mult=2.0)` — net Sharpe must degrade monotonically.
- **sweep.py**: grid over 1–2 params → tidy DataFrame (param cols + metric cols), parallel via ThreadPool, deterministic seeds.
- **synthetic.py bodies**: implement all Phase-0 signatures; lag-canary runs on `bid_ask_bounce_context` (deterministic), NOT real data.

## Family engines (WS-D1) — `qbt/strategy/lib/`

Six reusable engines; each strategy file is a thin parameterization (~50-120 lines):

1. `xs_rank.py` — cross-sectional: signal frame → rank/zscore → top/bottom fractile weights, sector-neutral option, skip-month option, rebalance calendar (`ctx.rebalance_dates`), long-only toggle (default ON for equities — shorting risk decision), vol-managed option.
2. `ts_signal.py` — time-series per instrument: signal ensemble (multi-lookback return sign / EWMA crossover / channel position), clamp [−1,1], inverse-vol scaling hooks, asset-class risk buckets.
3. `spread.py` — pair/basket state machine: formation window, hedge ratio (OLS β / cointegration), spread z-score, entry/exit/divergence-stop/half-life filter, β-weighted legs as weights output; supports N pairs concurrently.
4. `event_study.py` — event table (ctx.events[schema]) → position windows (entry day+k, hold m bars or until event2), overlapping-cohort netting, CAR reporting hooks.
5. `carry_curve.py` — futures chains/extras → basis, annualized slope, deseasonalized carry (same-month-next-year option), carry z-scores; consumes WS-A `ContinuousSeries` + chain metadata via ctx.extras.
6. `overlay.py` — `VolTargetOverlay(target, cap, floor, band)` implementing the Overlay protocol + `compose(weights_list, risk_weights)` for composite strategies.

D1 also ships `tests/strategy_lib/` unit tests on synthetic contexts and a template file `qbt/strategy/_template.py` used by `qbt new-strategy`.

## The 43 strategies — registry map

Groups: **A** = runs on MOEX data out of the box; **B** = working code fed by documented CSV schema (`qbt/data/schemas.py`), ships with `event_fixture` so it runs green with zero user data; **C** = parameterized but data-gated (`data_required` badge in UI). All 43 registered; none dropped.

| # | key | file (qbt/strategies/) | doc | grp | engine | out | WS |
|---|-----|------------------------|-----|-----|--------|-----|----|
| 1 | pairs_trading | pairs_trading.py | 01-arbitrage-relative-value/01 | A | spread | weights | D2 |
| 2 | stat_arb_residual | stat_arb_residual.py | 01-…/02 | A | spread+xs | weights | D2 |
| 3 | cash_and_carry | cash_and_carry.py | 01-…/03 | A | carry_curve | weights | D3 |
| 4 | etf_nav_arbitrage | etf_nav_arbitrage.py | 01-…/04 | C (`nav_series`) | spread | weights | D2 |
| 5 | merger_arbitrage | merger_arbitrage.py | 01-…/05 | B (`deals`) | event_study | orders | D2 |
| 6 | calendar_spread_rv | calendar_spread_rv.py | 01-…/06 | A | carry_curve | weights | D3 |
| 7 | convertible_arbitrage | convertible_arbitrage.py | 01-…/07 | C (`convert_terms`) | spread | weights | D3 |
| 8 | xs_equity_momentum | xs_equity_momentum.py | 02-momentum/01 | A | xs_rank | weights | D2 |
| 9 | ts_momentum | ts_momentum.py | 02-…/02 | A | ts_signal | weights | D3 |
| 10 | residual_momentum | residual_momentum.py | 02-…/03 | A | xs_rank | weights | D2 |
| 11 | industry_factor_momentum | industry_factor_momentum.py | 02-…/04 | A | xs_rank | weights | D2 |
| 12 | week52_high_momentum | week52_high_momentum.py | 02-…/05 | A | xs_rank | weights | D2 |
| 13 | dual_momentum | dual_momentum.py | 02-…/06 | A | ts_signal | weights | D3 |
| 14 | commodity_xs_momentum | commodity_xs_momentum.py | 02-…/07 | A | xs_rank | weights | D3 |
| 15 | managed_futures_trend | managed_futures_trend.py | 03-trend-following/01 | A | ts_signal | weights | D3 |
| 16 | breakout_channel | breakout_channel.py | 03-…/02 | A | orders | orders | D3 |
| 17 | trend_plus_carry | trend_plus_carry.py | 03-…/03 | A | ts+carry | weights | D3 |
| 18 | short_term_reversal | short_term_reversal.py | 04-mean-reversion-swing/01 | A | xs_rank | weights | D2 |
| 19 | index_panic_reversion | index_panic_reversion.py | 04-…/02 | A | orders | orders | D3 |
| 20 | swing_pullback | swing_pullback.py | 04-…/03 | A | orders | orders | D3 |
| 21 | overnight_intraday | overnight_intraday.py | 04-…/04 | A (daily O/C variants) | ts_signal | weights | D2 |
| 22 | fx_carry | fx_carry.py | 05-carry/01 (via FX futures basis) | A | carry_curve | weights | D3 |
| 23 | commodity_carry | commodity_carry.py | 05-…/02 | A | carry_curve | weights | D3 |
| 24 | bond_carry | bond_carry.py | 05-…/03 (OFZ; medium confidence) | A | carry_curve | weights | D3 |
| 25 | vol_carry | vol_carry.py | 05-…/04 | B (`vol_futures_curve`) | carry_curve | weights | D3 |
| 26 | cross_asset_carry | cross_asset_carry.py | 05-…/05 | A | compose | weights | D3 |
| 27 | variance_risk_premium | variance_risk_premium.py | 06-volatility/01 | B (`options_surface`) | event/carry | weights | D3 |
| 28 | vix_term_structure | vix_term_structure.py | 06-…/02 | B (`vol_futures_curve`) | state machine | weights | D3 |
| 29 | dispersion | dispersion.py | 06-…/03 | C (`options_surface` per-name) | spread | weights | D3 |
| 30 | vol_target_overlay | vol_target_overlay.py | 06-…/04 | A | Overlay + demo strat | weights | D3 |
| 31 | pead | pead.py | 07-event-driven/01 | B (`earnings_events`) | event_study | weights | D2 |
| 32 | index_rebalancing | index_rebalancing.py | 07-…/02 | B (`index_events`, auto-derive from ISS PIT where possible) | event_study | weights | D2 |
| 33 | buyback_insider | buyback_insider.py | 07-…/03 | B (`insider_buyback_events`) | event_study | weights | D2 |
| 34 | ipo_lockup | ipo_lockup.py | 07-…/04 | B (`ipo_lockups`) | event_study | orders | D2 |
| 35 | macro_announcement | macro_announcement.py | 07-…/05 | B (`macro_calendar`) | event_study | weights | D2 |
| 36 | equity_value_quality | equity_value_quality.py | 08-value-fundamental-factor/01 | B (`fundamentals_pit`) | xs_rank | weights | D2 |
| 37 | cross_asset_value | cross_asset_value.py | 08-…/02 | A | xs_rank | weights | D3 |
| 38 | low_vol_bab | low_vol_bab.py | 08-…/03 | A | xs_rank | weights | D2 |
| 39 | turn_of_month | turn_of_month.py | 09-flows-seasonality/01 | A | ts calendar | weights | D3 |
| 40 | roll_congestion | roll_congestion.py | 09-…/02 | B (`roll_calendar`) | carry_curve | weights | D3 |
| 41 | fundamental_seasonality | fundamental_seasonality.py | 09-…/03 | A/B | xs_rank | weights | D2 |
| 42 | funding_rate_arb | funding_rate_arb.py | 10-crypto-specific/01 | B (`funding_rates` + FileProvider bars) | carry | weights | D3 |
| 43 | cross_exchange_arb | cross_exchange_arb.py | 10-…/02 | C (`multi_venue_quotes`) | spread | weights | D3 |

Per-strategy depth: implement the doc's §3 baseline with `Param` entries carrying the doc's ranges + `source` refs; tier-1 (9, 15, 8, 10, 30, 19) get strategy-specific analytic tests; **every** strategy passes registry-level tests (lookahead harness over ≥3 cut dates, output shape, 2×-cost monotonicity, group B/C run green on `event_fixture` data).

## Web/API spec (WS-E)

- Endpoints: `GET /api/strategies` (metas incl. params/ranges/doc refs/data_required), `GET /api/strategies/{key}/doc` (rendered §3 of the md), `POST /api/runs` (RunRequest → run_id; job registry), `GET /api/runs/{id}` (status+progress), `GET /api/runs/{id}/result` (run JSON = `BacktestResult.to_run_json`), `GET /api/runs` (history + param diff), `POST /api/sweeps`, `GET /api/sweeps/{id}`, `GET /api/data/status` (coverage table), `POST /api/data/ensure`, `GET /api/data/health` (providers), `GET /api/bars` (candles for chart).
- UI single page, three panes: left form (auto-generated from params with range-bounded inputs, universe picker, dates, cost preset, lag, vol target, long-only toggle, overlay select, `data_required` badge), center charts (candles w/ trade markers for single-instrument, equity gross/net + **benchmark IMOEX overlay**, underwater), right/bottom tabs (Summary, Per-year incl. 2022 split, Costs, Exposure, Trades sortable+CSV, Episodes, Sweep heatmap, Data, History).
- Job registry: module-singleton ThreadPoolExecutor(2), results on disk `runs/<run_id>/`, progress field; document single-worker/no-reload constraint.
- Until WS-C lands, build against `FakeRunner` returning canned `BacktestResult` (WS-E owns `qbt/api/fake.py`, deleted at integration).
- CLI: `qbt data ensure --universe imoex --start 2015-01-01`, `qbt run <key> --param k=v --start --end`, `qbt sweep <key> --param a=1:10:1 --param b=...`, `qbt new-strategy <name>` (scaffolds from `qbt/strategy/_template.py`), `qbt dev record-fixtures --provider X`, `qbt serve`.

## OUT of MVP

Auth/multi-user, live trading/orders, streaming quotes, walk-forward UI, portfolio-builder UI (config-only), Monte-Carlo CIs, options analytics beyond schemas, orderbook viz, tick data, Docker, DB beyond parquet+sqlite, browser key management, i18n, impact-calibration UI.

## Key risk decisions (fixed for MVP)

1. 2022 halt: calendar marks it; per-year table splits at 2022-02-24; no masking.
2. Equities `shortable=False` default; long-only toggle default ON for equity XS strategies; short results labeled research-only.
3. Delisting return: config `delisting_return_pct` default −30% for suspensions, last price for corporate events — documented assumption.
4. Canonical daily close = main session; session flag stored.
5. Cache dir: `QBT_CACHE_DIR` else `%LOCALAPPDATA%/qbt` (Windows) / `~/.cache/qbt`.
6. ISS dividends have no announce dates ⇒ TR series fine, dividend-signal strategies must use `fundamentals_pit`.
7. Ticker aliases maintained in `configs/instruments/moex_aliases.yaml` (YNDX→YDEX, TCSG→T, POLY, FIVE→X5 …).
