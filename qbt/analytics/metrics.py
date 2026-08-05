"""Performance metrics (WS-C). NaN-robust; short series return NaNs, not crashes."""
from __future__ import annotations

import numpy as np
import pandas as pd

HALT_2022_START = pd.Timestamp("2022-02-24", tz="UTC")
HALT_2022_END = pd.Timestamp("2022-03-24", tz="UTC")


def _ann(r: pd.Series, ppy: float) -> tuple[float, float]:
    mu = r.mean() * ppy
    sd = r.std(ddof=1) * np.sqrt(ppy)
    return float(mu), float(sd)


def sharpe(r: pd.Series, rf: float = 0.0, ppy: float = 252.0) -> float:
    r = r.dropna()
    if len(r) < 3 or r.std(ddof=1) == 0:
        return float("nan")
    mu, sd = _ann(r - rf / ppy, ppy)
    return mu / sd


def sortino(r: pd.Series, ppy: float = 252.0) -> float:
    r = r.dropna()
    dn = r[r < 0]
    if len(r) < 3 or len(dn) == 0 or dn.std(ddof=1) == 0:
        return float("nan")
    return float(r.mean() * ppy / (dn.std(ddof=1) * np.sqrt(ppy)))


def cagr(r: pd.Series, ppy: float = 252.0) -> float:
    r = r.dropna()
    if not len(r):
        return float("nan")
    total = float((1 + r).prod())
    if total <= 0:
        return -1.0
    return total ** (ppy / len(r)) - 1.0


def summary(
    returns_net: pd.Series,
    returns_gross: pd.Series | None = None,
    positions: pd.DataFrame | None = None,
    trades: pd.DataFrame | None = None,
    rf: float = 0.0,
    ppy: float = 252.0,
) -> dict[str, float]:
    from qbt.analytics.drawdown import drawdown_periods, drawdown_series

    r = returns_net.dropna()
    eq = (1 + r).cumprod()
    dd = drawdown_series(eq)
    periods = drawdown_periods(eq)
    out: dict[str, float] = {
        "sharpe": sharpe(r, rf, ppy),
        "sortino": sortino(r, ppy),
        "cagr": cagr(r, ppy),
        "ann_vol": float(r.std(ddof=1) * np.sqrt(ppy)) if len(r) > 2 else float("nan"),
        "max_dd": float(dd.min()) if len(dd) else float("nan"),
        "dd_duration_days": float(max((p["duration"] for p in periods), default=0)),
        "skew": float(r.skew()) if len(r) > 3 else float("nan"),
        "kurtosis": float(r.kurtosis()) if len(r) > 3 else float("nan"),
        "hit_rate": float((r > 0).mean()) if len(r) else float("nan"),
        "t_stat": float(r.mean() / (r.std(ddof=1) / np.sqrt(len(r)))) if len(r) > 2 and r.std(ddof=1) > 0 else float("nan"),
        "n_obs": float(len(r)),
    }
    out["calmar"] = out["cagr"] / abs(out["max_dd"]) if out.get("max_dd") not in (None, 0) and np.isfinite(out["max_dd"]) and out["max_dd"] < 0 else float("nan")
    if returns_gross is not None:
        g = returns_gross.dropna()
        out["cagr_gross"] = cagr(g, ppy)
        out["cost_drag_bps_ann"] = float((g.mean() - r.reindex(g.index).fillna(0).mean()) * ppy * 1e4)
    if positions is not None and len(positions):
        w = positions.fillna(0.0)
        out["avg_gross"] = float(w.abs().sum(axis=1).mean())
        out["avg_net"] = float(w.sum(axis=1).mean())
        dw = w.diff()
        if len(dw):
            dw.iloc[0] = w.iloc[0]
        out["turnover_ann"] = float(0.5 * dw.abs().sum(axis=1).mean() * ppy)
    if trades is not None and len(trades) and "pnl" in trades:
        closed = trades.dropna(subset=["pnl"])
        out["n_trades"] = float(len(closed))
        if len(closed):
            out["trade_hit_rate"] = float((closed["pnl"] > 0).mean())
    yearly = r.groupby(r.index.year).apply(lambda x: float((1 + x).prod() - 1)) if len(r) else pd.Series(dtype=float)
    if len(yearly):
        out["best_year"] = float(yearly.max())
        out["worst_year"] = float(yearly.min())
    return out


def per_year_table(
    returns_gross: pd.Series,
    returns_net: pd.Series,
    costs: pd.DataFrame | None = None,
    trades: pd.DataFrame | None = None,
    ppy: float = 252.0,
) -> pd.DataFrame:
    """Per-calendar-year rows PLUS regime split rows at the 2022 halt (first-class)."""
    rows: list[dict] = []

    def block(label: str, mask: pd.Series) -> None:
        g, n_ = returns_gross[mask], returns_net[mask]
        if not len(n_.dropna()):
            return
        row = {
            "period": label,
            "gross": float((1 + g.fillna(0)).prod() - 1),
            "net": float((1 + n_.fillna(0)).prod() - 1),
            "sharpe_net": sharpe(n_, ppy=ppy),
            "max_dd": float(((1 + n_.fillna(0)).cumprod() / (1 + n_.fillna(0)).cumprod().cummax() - 1).min()),
            "n_obs": int(len(n_.dropna())),
        }
        row["cost_drag"] = row["gross"] - row["net"]
        if trades is not None and len(trades) and "ts" in trades:
            tts = pd.to_datetime(trades["ts"], utc=True)
            idx = n_.index
            row["n_trades"] = int(((tts >= idx.min()) & (tts <= idx.max())).sum()) if len(idx) else 0
        rows.append(row)

    idx = returns_net.index
    for year in sorted(set(idx.year)):
        block(str(year), idx.year == year)
    if len(idx) and idx.min() < HALT_2022_START and idx.max() > HALT_2022_END:
        block("pre-2022-02-24", idx < HALT_2022_START)
        block("post-2022-03-24", idx > HALT_2022_END)
    return pd.DataFrame(rows)
