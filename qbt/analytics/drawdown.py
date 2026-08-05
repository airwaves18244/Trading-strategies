"""Drawdown analytics (WS-C)."""
from __future__ import annotations

import pandas as pd


def drawdown_series(equity: pd.Series) -> pd.Series:
    eq = equity.dropna()
    return eq / eq.cummax() - 1.0


def max_drawdown(equity: pd.Series) -> float:
    dd = drawdown_series(equity)
    return float(dd.min()) if len(dd) else float("nan")


def drawdown_periods(equity: pd.Series, top_n: int = 10) -> list[dict]:
    """List of drawdown episodes: start (peak), trough, end (recovery or last), depth, duration (bars)."""
    eq = equity.dropna()
    if len(eq) < 2:
        return []
    dd = drawdown_series(eq)
    out: list[dict] = []
    in_dd = False
    start = trough = None
    depth = 0.0
    for ts, v in dd.items():
        if v < 0 and not in_dd:
            in_dd, start, trough, depth = True, ts, ts, v
        elif in_dd:
            if v < depth:
                depth, trough = v, ts
            if v == 0:
                out.append({"start": start, "trough": trough, "end": ts,
                            "depth": float(depth),
                            "duration": int(dd.index.get_loc(ts) - dd.index.get_loc(start))})
                in_dd = False
    if in_dd:
        out.append({"start": start, "trough": trough, "end": dd.index[-1],
                    "depth": float(depth),
                    "duration": int(len(dd) - 1 - dd.index.get_loc(start))})
    out.sort(key=lambda p: p["depth"])
    return out[:top_n]
