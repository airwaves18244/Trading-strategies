"""FakeRunner — deterministic canned results for the web/API layer.

Used (a) as the demo backend (`qbt serve --fake` / `create_app(runner="fake")`)
so the terminal is fully clickable before qbt.engine / qbt.data land, and
(b) by tests/api/** so they never depend on the real pipeline.

Hard rule: this module imports ONLY qbt.engine.result (the frozen dataclass +
column constants) and qbt.api.schemas -- never qbt.engine.weights/orders/
runner or qbt.data.* (those belong to WS-C/WS-A/WS-B and may not exist yet).
Every BacktestResult here is built by hand with pandas/numpy.

Determinism: every method is a pure function of its inputs (seeded via a
sha256 hash of the relevant request fields), so the same request always
produces the same numbers -- convenient for tests and for demo repeatability.
"""
from __future__ import annotations

import hashlib
import itertools
import time
from datetime import datetime, timezone
from typing import Any, Callable

import numpy as np
import pandas as pd

from qbt.engine.result import (
    COST_COLUMNS, EXPOSURE_COLUMNS, TRADES_COLUMNS, BacktestResult, RunMeta,
)

#: fixed demo universe -- three liquid MOEX blue chips
DEFAULT_SYMBOLS: tuple[str, ...] = ("SBER", "GAZP", "LKOH")
_TRADE_REASONS = ("signal", "rebalance", "stop", "take", "time_stop")
_SPLIT_DATE = pd.Timestamp("2022-02-24", tz="UTC")


def _seed(*parts: Any) -> int:
    blob = "|".join(repr(p) for p in parts).encode("utf-8")
    return int(hashlib.sha256(blob).hexdigest()[:8], 16)


def _calendar(start: str, end: str) -> pd.DatetimeIndex:
    cal = pd.bdate_range(start, end, tz="UTC")
    if len(cal) < 30:
        # keep every fake result usable even for tiny/degenerate ranges
        cal = pd.bdate_range(end=end or "2023-12-29", periods=60, tz="UTC")
    return cal


def _gbm_close(seed: int, index: pd.DatetimeIndex, mu: float = 0.0005,
               sigma: float = 0.018, s0: float = 100.0,
               crash: bool = False) -> pd.Series:
    """Deterministic GBM-ish close price path, optionally with a scripted
    2022-style drawdown so the equity/drawdown charts have something to show.
    """
    rng = np.random.default_rng(seed)
    n = len(index)
    shocks = rng.normal(mu, sigma, size=n)
    if crash:
        dd_start = n // 3
        dd_len = max(1, min(18, n // 8))
        shocks[dd_start:dd_start + dd_len] -= 0.028
        # partial recovery drift afterward
        shocks[dd_start + dd_len:dd_start + dd_len + 25] += 0.004
    price = s0 * np.cumprod(1.0 + shocks)
    return pd.Series(price, index=index, name="close")


def _ohlcv_from_close(seed: int, close: pd.Series) -> pd.DataFrame:
    rng = np.random.default_rng(seed + 1)
    n = len(close)
    prev = close.shift(1).bfill()
    open_ = prev * (1 + rng.normal(0, 0.002, n))
    hi_noise = np.abs(rng.normal(0.004, 0.003, n))
    lo_noise = np.abs(rng.normal(0.004, 0.003, n))
    high = np.maximum(open_, close) * (1 + hi_noise)
    low = np.minimum(open_, close) * (1 - lo_noise)
    volume = rng.lognormal(mean=13.0, sigma=0.4, size=n)
    return pd.DataFrame({
        "open": open_.values, "high": high, "low": low,
        "close": close.values, "volume": volume,
    }, index=close.index)


def _weights_frame(seed: int, index: pd.DatetimeIndex, symbols: tuple[str, ...],
                    long_only: bool = False) -> pd.DataFrame:
    rng = np.random.default_rng(seed + 2)
    n, k = len(index), len(symbols)
    t = np.linspace(0, 6 * np.pi, n)
    cols = {}
    for i, sym in enumerate(symbols):
        base = 0.25 * np.sin(t + i * 2.1) + rng.normal(0, 0.03, n).cumsum() * 0.01
        base = np.clip(base, -0.6, 0.6)
        if long_only:
            base = np.abs(base) * 0.6 + 0.05
        cols[sym] = base
    w = pd.DataFrame(cols, index=index)
    # monthly-ish holding: forward-fill a monthly sample to avoid daily churn
    sample = w.resample("W-FRI").last().reindex(index, method="ffill").bfill()
    return sample.round(6)


def _costs_frame(seed: int, weights: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(seed + 3)
    turnover = weights.diff().abs().sum(axis=1).fillna(0.0)
    n = len(weights)
    commission = turnover * 0.0004
    spread = turnover * 0.0003
    impact = turnover * (0.0001 + 0.0002 * rng.random(n))
    gross_short = weights.clip(upper=0).abs().sum(axis=1)
    borrow = gross_short * (0.03 / 252)
    return pd.DataFrame({
        "commission": commission.values, "spread": spread.values,
        "impact": impact.values, "borrow": borrow.values,
    }, index=weights.index)


def _exposure_frame(weights: pd.DataFrame) -> pd.DataFrame:
    gross = weights.abs().sum(axis=1)
    net = weights.sum(axis=1)
    long = weights.clip(lower=0).sum(axis=1)
    short = -weights.clip(upper=0).sum(axis=1)
    n_positions = (weights.abs() > 1e-6).sum(axis=1)
    return pd.DataFrame({
        "gross": gross, "net": net, "long": long, "short": short,
        "n_positions": n_positions,
    })


def _trades_ledger(seed: int, index: pd.DatetimeIndex, symbols: tuple[str, ...],
                    closes: dict[str, pd.Series], n_trades: int = 40) -> pd.DataFrame:
    rng = np.random.default_rng(seed + 4)
    n = len(index)
    pick = np.sort(rng.choice(n, size=min(n_trades, n), replace=False))
    rows = []
    for j, i in enumerate(pick):
        ts = index[i]
        sym = symbols[int(rng.integers(0, len(symbols)))]
        side = int(rng.choice([-1, 1]))
        price = float(closes[sym].iloc[i])
        qty = float(rng.integers(10, 500))
        notional = round(qty * price, 2)
        cost_bps = float(rng.uniform(5, 25))
        reason = _TRADE_REASONS[int(rng.integers(0, len(_TRADE_REASONS)))]
        pnl = float(rng.normal(0, 1) * notional * 0.01 * side)
        rows.append({
            "ts": ts, "symbol": sym, "side": side, "qty": qty, "price": round(price, 4),
            "notional": notional, "cost_bps": round(cost_bps, 2), "reason": reason,
            "tag": f"ep-{j // 4}", "pnl": round(pnl, 2),
        })
    return pd.DataFrame(rows, columns=list(TRADES_COLUMNS))


def _per_year_table(returns_gross: pd.Series, returns_net: pd.Series,
                     costs: pd.DataFrame, trades: pd.DataFrame) -> pd.DataFrame:
    idx = returns_net.index
    label = pd.Series(idx.year.astype(str), index=idx)
    is_2022 = idx.year == 2022
    if is_2022.any():
        pre = is_2022 & (idx < _SPLIT_DATE)
        post = is_2022 & (idx >= _SPLIT_DATE)
        label = label.mask(pre, "2022-pre").mask(post, "2022-post")
    trade_ts = pd.to_datetime(trades["ts"]) if len(trades) else pd.Series([], dtype="datetime64[ns, UTC]")
    rows = []
    for lab in sorted(label.unique(), key=lambda s: (int(s[:4]), s)):
        sel = label == lab
        rg, rn = returns_gross[sel], returns_net[sel]
        if not len(rn):
            continue
        eq = (1 + rn).cumprod()
        dd = float((eq / eq.cummax() - 1.0).min())
        sharpe_net = float(rn.mean() / rn.std() * np.sqrt(252)) if rn.std() > 0 else 0.0
        lo, hi = idx[sel].min(), idx[sel].max()
        n_trades = int(trade_ts.between(lo, hi).sum()) if len(trade_ts) else 0
        rows.append({
            "year": lab,
            "gross": float((1 + rg).prod() - 1),
            "net": float((1 + rn).prod() - 1),
            "cost_drag": float(costs.loc[sel].sum().sum()),
            "sharpe_net": round(sharpe_net, 3),
            "max_dd": round(dd, 4),
            "n_trades": n_trades,
        })
    return pd.DataFrame(rows, columns=["year", "gross", "net", "cost_drag", "sharpe_net", "max_dd", "n_trades"])


def _dd_duration_days(equity: pd.Series) -> int:
    peak = equity.cummax()
    underwater = equity < peak
    if not underwater.any():
        return 0
    # longest run of consecutive underwater days, in calendar days
    groups = (~underwater).cumsum()
    longest = 0
    for _, grp in underwater.groupby(groups):
        if grp.any():
            span = (grp.index[-1] - grp.index[0]).days + 1
            longest = max(longest, span)
    return int(longest)


def _summary_metrics(returns_net: pd.Series, equity: pd.Series, weights: pd.DataFrame,
                      costs: pd.DataFrame, exposure: pd.DataFrame,
                      per_year: pd.DataFrame) -> dict[str, float]:
    n = len(returns_net)
    mu, sd = float(returns_net.mean()), float(returns_net.std())
    sharpe = mu / sd * np.sqrt(252) if sd > 0 else 0.0
    downside = returns_net[returns_net < 0]
    dsd = float(downside.std()) if len(downside) > 1 else 0.0
    sortino = mu / dsd * np.sqrt(252) if dsd > 0 else 0.0
    cagr = float((equity.iloc[-1] / equity.iloc[0]) ** (252 / max(n, 1)) - 1)
    ann_vol = sd * np.sqrt(252)
    max_dd = float((equity / equity.cummax() - 1).min())
    calmar = cagr / abs(max_dd) if max_dd else 0.0
    turnover_ann = float(weights.diff().abs().sum(axis=1).mean() * 252)
    cost_drag_bps_ann = float(costs.sum(axis=1).mean() * 252 * 1e4)
    net_col = per_year["net"] if "net" in per_year else pd.Series([0.0])
    return {
        "sharpe": round(sharpe, 3),
        "sortino": round(sortino, 3),
        "cagr": round(cagr, 4),
        "ann_vol": round(float(ann_vol), 4),
        "max_dd": round(max_dd, 4),
        "dd_duration_days": _dd_duration_days(equity),
        "calmar": round(float(calmar), 3),
        "skew": round(float(returns_net.skew()), 3),
        "kurtosis": round(float(returns_net.kurt()), 3),
        "hit_rate": round(float((returns_net > 0).mean()), 4),
        "turnover_ann": round(turnover_ann, 3),
        "avg_gross_exposure": round(float(exposure["gross"].mean()), 4),
        "avg_net_exposure": round(float(exposure["net"].mean()), 4),
        "cost_drag_bps_ann": round(cost_drag_bps_ann, 2),
        "t_stat": round(sharpe * np.sqrt(n / 252), 3) if n else 0.0,
        "best_year": round(float(net_col.max()), 4) if len(net_col) else None,
        "worst_year": round(float(net_col.min()), 4) if len(net_col) else None,
    }


class FakeRunner:
    """Deterministic canned-result engine. See module docstring."""

    name = "fake"

    # ---------------- backtest run ----------------

    def run(self, req: Any, run_id: str,
            progress_cb: Callable[[float], None] | None = None) -> BacktestResult:
        def tick(p: float) -> None:
            if progress_cb is not None:
                progress_cb(p)
                time.sleep(0.02)  # small, visible steps for progress-polling UIs

        tick(0.05)
        params = dict(getattr(req, "params", {}) or {})
        seed = _seed(req.strategy_key, sorted(params.items()), req.universe, req.start, req.end)
        index = _calendar(req.start, req.end)
        long_only = bool(getattr(req, "long_only", False) or False)

        tick(0.2)
        closes = {sym: _gbm_close(_seed(seed, sym), index, crash=True) for sym in DEFAULT_SYMBOLS}
        weights = _weights_frame(seed, index, DEFAULT_SYMBOLS, long_only=long_only)
        positions = weights.copy()  # fake: realized == target

        tick(0.4)
        costs = _costs_frame(seed, weights)
        exposure = _exposure_frame(weights)
        per_symbol_ret = pd.DataFrame({s: c.pct_change(fill_method=None) for s, c in closes.items()}).fillna(0.0)
        returns_gross = (weights.shift(1).fillna(0.0) * per_symbol_ret).sum(axis=1)
        returns_net = returns_gross - costs.sum(axis=1)
        equity = (1 + returns_net).cumprod()
        equity.iloc[0] = 1.0 * (1 + returns_net.iloc[0])

        tick(0.6)
        trades = _trades_ledger(seed, index, DEFAULT_SYMBOLS, closes)
        per_year = _per_year_table(returns_gross, returns_net, costs, trades)
        metrics = _summary_metrics(returns_net, equity, weights, costs, exposure, per_year)

        tick(0.8)
        bench_close = _gbm_close(_seed(seed, "IMOEX"), index, mu=0.0003, sigma=0.012, crash=True)
        bench_ret = bench_close.pct_change(fill_method=None).fillna(0.0)
        benchmark_equity = (1 + bench_ret).cumprod()

        meta = RunMeta(
            run_id=run_id, strategy_key=req.strategy_key, params=params,
            universe=req.universe, start=str(req.start), end=str(req.end), freq=req.freq,
            cost_preset=req.cost_preset, execution_lag=req.execution_lag, overlay=req.overlay,
            created_at=datetime.now(timezone.utc).isoformat(), engine="weights",
            notes="FakeRunner canned result -- no real data/engine involved",
        )
        tick(0.95)
        return BacktestResult(
            equity=equity, returns_gross=returns_gross, returns_net=returns_net,
            weights=weights, positions=positions, trades=trades, costs=costs,
            exposure=exposure, metrics=metrics, per_year=per_year, meta=meta,
            benchmark_equity=benchmark_equity,
        )

    # ---------------- sweep ----------------

    def sweep(self, req: Any, run_id: str,
              progress_cb: Callable[[float], None] | None = None) -> pd.DataFrame:
        grid: dict[str, list[Any]] = dict(req.grid)
        keys = list(grid.keys())
        combos = list(itertools.product(*[grid[k] for k in keys])) if keys else [()]
        rows = []
        for j, combo in enumerate(combos):
            combo_params = dict(zip(keys, combo))
            seed = _seed(req.strategy_key, sorted(combo_params.items()), req.universe)
            index = _calendar(req.start, req.end)
            rng = np.random.default_rng(seed)
            rets = pd.Series(rng.normal(0.0004, 0.011, len(index)), index=index)
            eq = (1 + rets).cumprod()
            sharpe = float(rets.mean() / rets.std() * np.sqrt(252)) if rets.std() > 0 else 0.0
            cagr = float(eq.iloc[-1] ** (252 / len(eq)) - 1)
            max_dd = float((eq / eq.cummax() - 1).min())
            row = dict(combo_params)
            row.update({"sharpe_net": round(sharpe, 3), "cagr": round(cagr, 4),
                        "max_dd": round(max_dd, 4), "calmar": round(cagr / abs(max_dd), 3) if max_dd else 0.0})
            rows.append(row)
            if progress_cb is not None:
                progress_cb((j + 1) / len(combos))
        return pd.DataFrame(rows)

    # ---------------- data endpoints ----------------

    def data_status(self) -> list[dict[str, Any]]:
        now = datetime.now(timezone.utc).isoformat()
        out = []
        for sym in (*DEFAULT_SYMBOLS, "IMOEX"):
            seed = _seed("status", sym)
            rng = np.random.default_rng(seed)
            rows = int(rng.integers(1500, 2600))
            out.append({
                "symbol": sym, "freq": "1d",
                "first_ts": "2015-01-05T00:00:00+00:00", "last_ts": "2023-12-29T00:00:00+00:00",
                "rows": rows, "updated_at": now, "provider": "fake",
            })
        return out

    def data_health(self) -> list[dict[str, Any]]:
        return [
            {"provider": "moex_iss", "ok": True, "detail": "fake: reachable (demo mode)"},
            {"provider": "algopack", "ok": True, "detail": "fake: reachable (demo mode)"},
            {"provider": "finam", "ok": True, "detail": "fake: reachable (demo mode)"},
            {"provider": "files", "ok": True, "detail": "fake: local import ready"},
        ]

    def ensure(self, req: Any, progress_cb: Callable[[float], None] | None = None) -> dict[str, Any]:
        symbols = req.symbols or list(DEFAULT_SYMBOLS)
        if progress_cb is not None:
            for p in (0.25, 0.5, 0.75, 1.0):
                progress_cb(p)
                time.sleep(0.02)
        return {
            "status": "ok", "provider": req.provider, "freq": req.freq,
            "symbols": symbols, "rows_added": len(symbols) * 250,
            "note": "FakeRunner: no real data was fetched (demo mode)",
        }

    def bars(self, symbol: str, freq: str, start: str, end: str) -> list[dict[str, Any]]:
        index = _calendar(start, end)
        close = _gbm_close(_seed("bars", symbol, freq), index, crash=True)
        ohlcv = _ohlcv_from_close(_seed("bars", symbol, freq), close)
        return [
            {
                "time": int(pd.Timestamp(ts).timestamp()),
                "open": round(float(r.open), 4), "high": round(float(r.high), 4),
                "low": round(float(r.low), 4), "close": round(float(r.close), 4),
                "volume": round(float(r.volume), 1),
            }
            for ts, r in ohlcv.iterrows()
        ]


__all__ = ["FakeRunner", "DEFAULT_SYMBOLS"]
