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
    """Drawdown episodes, deepest first.

    Keys: start (PEAK — the last bar at the old high), trough, end, depth,
    duration and recovery in BARS, and `recovered` — False for an episode still
    under water at the last bar, whose `end` is then the last bar, NOT a
    recovery (run.json v2 renders end/recovery_days as null in that case).

    Positional bookkeeping (not `get_loc`) because after a recovery the peak
    must advance to the recovery bar; carrying the stale peak forward started
    every episode after the first one too early.
    """
    eq = equity.dropna()
    if len(eq) < 2:
        return []
    dd = drawdown_series(eq)
    idx, vals = dd.index, dd.to_numpy(dtype=float)
    out: list[dict] = []
    in_dd = False
    peak_i = trough_i = 0
    depth = 0.0
    for i, v in enumerate(vals):
        if not in_dd:
            if v >= 0:
                peak_i = i
                continue
            in_dd, trough_i, depth = True, i, v
        if v < depth:
            depth, trough_i = v, i
        if v >= 0:
            out.append({"start": idx[peak_i], "trough": idx[trough_i], "end": idx[i],
                        "depth": float(depth), "duration": int(i - peak_i),
                        "recovery": int(i - trough_i), "recovered": True})
            in_dd, peak_i = False, i
    if in_dd:
        out.append({"start": idx[peak_i], "trough": idx[trough_i], "end": idx[-1],
                    "depth": float(depth), "duration": int(len(vals) - 1 - peak_i),
                    "recovery": None, "recovered": False})
    out.sort(key=lambda p: p["depth"])
    return out[:top_n]
