"""run.json v2 report blocks (WS-A, docs/ui-upgrade.md §1).

Pure functions + `extend_run_json`. WHY pure: the same numbers are needed from a
BacktestResult (terminal), from raw series (tests) and eventually from a saved
run, so nothing here may reach for engine state. Every block degrades to
`null`/`[]` on empty, short or all-NaN input instead of raising — the UI always
gets the key.

Everything JSON-facing goes through `_f`: NaN/±inf become `null` because
`JSON.parse` rejects the `NaN`/`Infinity` tokens `json.dumps` would emit.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from qbt.analytics.attribution import instrument_contribution
from qbt.analytics.drawdown import drawdown_periods
from qbt.analytics.metrics import _ann, cagr, sharpe

#: contract fixes the annualization at 252 regardless of ctx.ann_factor
PPY = 252.0
ROLL_WINDOW = 252
MAX_ROLL_POINTS = 1500
MAX_ATTRIBUTION_ROWS = 50
MAX_DRAWDOWNS = 10
IS_FRACTION = 0.7


def _f(x: Any) -> float | None:
    """JSON-safe float: None/NaN/±inf -> None."""
    if x is None:
        return None
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if np.isfinite(v) else None


def _date(ts: Any) -> str | None:
    try:
        return pd.Timestamp(ts).strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        return None


def _unix(ts: Any) -> int:
    return int(pd.Timestamp(ts).timestamp())


def _subsample(frame: pd.DataFrame, max_points: int) -> pd.DataFrame:
    """Even index subsample — all rolling series must be downsampled together."""
    if max_points and len(frame) > max_points:
        return frame.iloc[np.linspace(0, len(frame) - 1, max_points).astype(int)]
    return frame


# --------------------------------------------------------------------------- #
# blocks                                                                       #
# --------------------------------------------------------------------------- #

def monthly_table(returns: pd.Series) -> dict[str, Any]:
    """Calendar month returns compounded within the month; `null` = no data."""
    r = pd.Series(returns).dropna()
    if not len(r):
        return {"years": [], "cells": [], "totals": []}
    idx = pd.DatetimeIndex(r.index)
    comp = (1.0 + r).groupby([idx.year, idx.month]).prod() - 1.0
    years = sorted({int(y) for y, _ in comp.index})
    cells: list[list[float | None]] = []
    totals: list[float | None] = []
    for y in years:
        row: list[float | None] = [None] * 12
        for (yy, mm), v in comp.items():
            if int(yy) == y:
                row[int(mm) - 1] = _f(v)
        cells.append(row)
        totals.append(_f((1.0 + r[idx.year == y]).prod() - 1.0))
    return {"years": years, "cells": cells, "totals": totals}


def rolling_stats(
    returns: pd.Series,
    bench_returns: pd.Series | None = None,
    window: int = ROLL_WINDOW,
    max_points: int = MAX_ROLL_POINTS,
    ppy: float = PPY,
) -> dict[str, Any]:
    """Rolling sharpe/vol (+beta vs benchmark). Warm-up points are skipped, not
    null-padded, so `ts` and the value arrays always have equal length."""
    r = pd.Series(returns).dropna()
    has_bench = bench_returns is not None
    if len(r) < window or window < 2:
        return {"ts": [], "sharpe": [], "vol": [], "beta": [] if has_bench else None}

    sd = r.rolling(window).std(ddof=1)
    frame = pd.DataFrame({
        "sharpe": r.rolling(window).mean() / sd * np.sqrt(ppy),
        "vol": sd * np.sqrt(ppy),
    })
    if has_bench:
        rb = pd.Series(bench_returns).reindex(r.index)
        var = rb.rolling(window).var(ddof=1)
        frame["beta"] = r.rolling(window).cov(rb) / var.where(var > 0)
    frame = _subsample(frame.iloc[window - 1:], max_points)

    return {
        "ts": [_unix(t) for t in frame.index],
        "sharpe": [_f(v) for v in frame["sharpe"]],
        "vol": [_f(v) for v in frame["vol"]],
        "beta": [_f(v) for v in frame["beta"]] if has_bench else None,
    }


def benchmark_stats(
    returns: pd.Series,
    bench_equity: pd.Series | None,
    symbol: str | None = None,
    ppy: float = PPY,
) -> dict[str, Any] | None:
    """Benchmark's own risk/return plus the strategy-vs-benchmark pair stats."""
    if bench_equity is None:
        return None
    be = pd.Series(bench_equity).dropna()
    if len(be) < 2:
        return None
    rb = be.pct_change().dropna()
    name = symbol or (getattr(bench_equity, "name", None) or "benchmark")
    out: dict[str, Any] = {
        "symbol": str(name),
        "sharpe": _f(sharpe(rb, ppy=ppy)),
        "cagr": _f(cagr(rb, ppy=ppy)),
        "ann_vol": _f(rb.std(ddof=1) * np.sqrt(ppy)) if len(rb) > 2 else None,
        "max_dd": _f((be / be.cummax() - 1.0).min()),
        "alpha_ann": None, "beta": None, "corr": None, "te_ann": None, "ir": None,
    }
    both = pd.DataFrame({"r": pd.Series(returns).dropna(), "rb": rb}).dropna()
    if len(both) > 2:
        a, b = both["r"], both["rb"]
        var = float(b.var(ddof=1))
        beta = float(a.cov(b) / var) if var > 0 else float("nan")
        d = a - b
        mu_d, sd_d = _ann(d, ppy)
        out.update({
            "beta": _f(beta),
            "alpha_ann": _f((a.mean() - beta * b.mean()) * ppy),
            "corr": _f(a.corr(b)),
            "te_ann": _f(sd_d),
            "ir": _f(mu_d / sd_d) if sd_d else None,
        })
    return out


def _avg_hold_days(trades: pd.DataFrame) -> float | None:
    """FIFO entry/exit pairing per symbol; None when the ledger has no pairs
    (the weight engine emits rebalance rows, not round trips)."""
    if not {"ts", "symbol", "reason", "pnl"} <= set(trades.columns):
        return None
    df = trades[["symbol", "reason", "pnl"]].copy()
    df["ts"] = pd.to_datetime(trades["ts"], utc=True, errors="coerce")
    df = df.dropna(subset=["ts"]).sort_values("ts")
    holds: list[float] = []
    for _, grp in df.groupby("symbol", sort=False):
        opened: list[pd.Timestamp] = []
        for t, reason, pnl in zip(grp["ts"], grp["reason"], grp["pnl"]):
            if reason == "entry":
                opened.append(t)
            elif pd.notna(pnl) and opened:
                holds.append((t - opened.pop(0)).total_seconds() / 86400.0)
    return _f(np.mean(holds)) if holds else None


def trade_stats(trades: pd.DataFrame | None,
                initial_nav: float = 1.0) -> dict[str, Any] | None:
    """Round-trip statistics; None unless the ledger carries realized pnl.

    Ledger pnl is in NAV currency units, so with initial_nav=1e6 an avg_win of
    11418 is rubles, not a fraction — divide by initial_nav so the contract's
    "returns are decimals" rule holds for every engine.
    """
    if trades is None or not len(trades) or "pnl" not in trades.columns:
        return None
    closed = trades[trades["pnl"].notna()]
    if not len(closed):
        return None
    pnl = closed["pnl"].astype(float) / (initial_nav if initial_nav else 1.0)
    wins, losses = pnl[pnl > 0], pnl[pnl < 0]
    gross_loss = float(-losses.sum())
    return {
        "n": int(len(pnl)),
        "win_rate": _f((pnl > 0).mean()),
        # None (not inf) when nothing lost — JSON.parse rejects Infinity
        "profit_factor": _f(wins.sum() / gross_loss) if gross_loss > 0 else None,
        "avg_win": _f(wins.mean()) if len(wins) else None,
        "avg_loss": _f(losses.mean()) if len(losses) else None,
        "expectancy": _f(pnl.mean()),
        "avg_hold_days": _avg_hold_days(trades),
        "best": _f(pnl.max()),
        "worst": _f(pnl.min()),
    }


def drawdown_rows(equity: pd.Series, top_n: int = MAX_DRAWDOWNS) -> list[dict[str, Any]]:
    """`drawdown_periods` mapped to the contract shape (deepest first).

    `days`/`recovery_days` are BAR counts: the engine is daily-bar based and the
    duration convention must match `metrics.dd_duration_days`.
    """
    rows = []
    for p in drawdown_periods(pd.Series(equity).dropna(), top_n=top_n):
        recovered = bool(p.get("recovered", True))
        rows.append({
            "start": _date(p["start"]),
            "trough": _date(p["trough"]),
            "end": _date(p["end"]) if recovered else None,
            "depth": _f(p["depth"]),
            "days": int(p["duration"]),
            "recovery_days": int(p["recovery"]) if recovered and p.get("recovery") is not None else None,
        })
    return rows


def attribution_rows(
    weights: pd.DataFrame | None,
    returns: pd.DataFrame | pd.Series | None = None,
    trades: pd.DataFrame | None = None,
    top_n: int = MAX_ATTRIBUTION_ROWS,
) -> list[dict[str, Any]]:
    """Per-symbol contribution to NAV, sorted by pnl desc.

    CONTRACT DEVIATION (documented, docs/ui-upgrade.md §1): BacktestResult does
    not carry the per-symbol return matrix, so exactness depends on what the
    caller can supply — hence the ladder:
      1. `returns` is a DataFrame  -> exact  Σ_t w_i,t · r_i,t;
      2. ledger has realized pnl   -> exact realized P&L per symbol (order engine);
      3. `returns` is a Series     -> the day's portfolio return split across names
         by share of gross exposure. This is a capital-usage proxy, not a true
         per-name P&L: it ranks who carried the book, not who was right.
    `avg_weight` is the mean ABSOLUTE weight (capital usage); a signed mean is
    ~0 for anything that flips sides and would read as "no position".
    """
    w = pd.DataFrame(weights).fillna(0.0) if weights is not None and len(weights) else pd.DataFrame()
    avg_w = w.abs().mean() if len(w.columns) else pd.Series(dtype=float)

    has_trades = trades is not None and len(trades) and "symbol" in trades.columns
    n_tr = trades.groupby("symbol").size() if has_trades else pd.Series(dtype=int)

    pnl = pd.Series(dtype=float)
    if isinstance(returns, pd.DataFrame) and len(w.columns):
        pnl = instrument_contribution(w, returns, top_n=len(w.columns))["contribution"]
    elif has_trades and "pnl" in trades.columns and trades["pnl"].notna().any():
        pnl = trades.dropna(subset=["pnl"]).groupby("symbol")["pnl"].sum()
    elif isinstance(returns, pd.Series) and len(w.columns):
        gross = w.abs().sum(axis=1)
        share = w.abs().div(gross.where(gross > 0), axis=0).fillna(0.0)
        pnl = share.mul(pd.Series(returns).reindex(share.index).fillna(0.0), axis=0).sum()

    symbols = set(avg_w.index) | set(pnl.index) | set(n_tr.index)
    rows = []
    for sym in symbols:
        aw, p = _f(avg_w.get(sym)), _f(pnl.get(sym))
        n = int(n_tr.get(sym, 0))
        if not aw and not p and not n:
            continue                      # never held, never traded — noise row
        rows.append({"symbol": str(sym), "pnl": p, "avg_weight": aw, "n_trades": n})
    rows.sort(key=lambda x: (x["pnl"] is not None, x["pnl"] or 0.0), reverse=True)
    return rows[:top_n]


# --------------------------------------------------------------------------- #
# payload                                                                      #
# --------------------------------------------------------------------------- #

def extend_run_json(result: Any, out: dict[str, Any],
                    max_points: int = MAX_ROLL_POINTS) -> dict[str, Any]:
    """Add every run.json v2 key to `out` (mutates and returns it).

    Called by BacktestResult.to_run_json, so both runners get v2 for free.
    """
    r = result.returns_net.dropna()
    bench = result.benchmark_equity
    bench_r = pd.Series(bench).dropna().pct_change().dropna() if bench is not None else None

    out["benchmark_stats"] = benchmark_stats(r, bench)
    out["monthly"] = monthly_table(r)
    out["drawdowns"] = drawdown_rows(result.equity)
    out["rolling"] = rolling_stats(r, bench_r, max_points=max_points)
    out["attribution"] = attribution_rows(result.weights, r, result.trades)
    eq = pd.Series(result.equity).dropna()
    out["trade_stats"] = trade_stats(result.trades,
                                     initial_nav=float(eq.iloc[0]) if len(eq) else 1.0)
    return out


def is_oos_sharpe(returns: pd.Series, ppy: float = PPY,
                  is_fraction: float = IS_FRACTION) -> tuple[float | None, float | None]:
    """Sharpe of the first `is_fraction` of the sample vs the rest — the cheap
    overfit canary for sweeps: a cell that only works in-sample is curve fit."""
    r = pd.Series(returns).dropna()
    k = int(len(r) * is_fraction)
    if len(r) < 6 or k < 3 or len(r) - k < 3:
        return None, None
    return _f(sharpe(r.iloc[:k], ppy=ppy)), _f(sharpe(r.iloc[k:], ppy=ppy))
