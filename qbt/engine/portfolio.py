"""Shared accounting helpers used by both engines (WS-C)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from qbt.engine.result import EXPOSURE_COLUMNS

WEIGHT_TOL = 1e-9


def exposure_frame(weights: pd.DataFrame) -> pd.DataFrame:
    """gross/net/long/short/n_positions per day from a weights matrix."""
    w = weights.fillna(0.0)
    long = w.clip(lower=0).sum(axis=1)
    short = w.clip(upper=0).sum(axis=1)
    out = pd.DataFrame({
        "gross": w.abs().sum(axis=1),
        "net": w.sum(axis=1),
        "long": long,
        "short": short,
        "n_positions": (w.abs() > WEIGHT_TOL).sum(axis=1).astype(float),
    })
    return out.loc[:, list(EXPOSURE_COLUMNS)]


def turnover_series(weights: pd.DataFrame) -> pd.Series:
    """One-sided turnover per day: 0.5 * sum|Δw| (buys+sells)/2."""
    dw = weights.fillna(0.0).diff()
    if len(dw):
        dw.iloc[0] = weights.iloc[0].fillna(0.0)
    return 0.5 * dw.abs().sum(axis=1)


def trades_from_weight_changes(
    weights: pd.DataFrame, close: pd.DataFrame, nav: pd.Series,
    cost_bps: pd.DataFrame | None = None, tol: float = 1e-6,
) -> pd.DataFrame:
    """Aggregate ledger: one row per (ts, symbol) where the weight changed."""
    dw = weights.fillna(0.0).diff()
    if len(dw):
        dw.iloc[0] = weights.iloc[0].fillna(0.0)
    rows: list[dict] = []
    changed = dw.abs() > tol
    for ts in dw.index[changed.any(axis=1)]:
        row = dw.loc[ts]
        for sym in row.index[changed.loc[ts]]:
            delta = float(row[sym])
            px = float(close.at[ts, sym]) if sym in close.columns and pd.notna(close.at[ts, sym]) else np.nan
            notional = abs(delta) * float(nav.loc[ts]) if ts in nav.index else abs(delta)
            rows.append({
                "ts": ts, "symbol": sym, "side": int(np.sign(delta)),
                "qty": notional / px if px and np.isfinite(px) and px > 0 else np.nan,
                "price": px, "notional": notional,
                "cost_bps": float(cost_bps.at[ts, sym]) if cost_bps is not None
                and sym in cost_bps.columns and pd.notna(cost_bps.at[ts, sym]) else np.nan,
                "reason": "signal", "tag": "", "pnl": np.nan,
            })
    from qbt.engine.result import TRADES_COLUMNS
    return pd.DataFrame(rows, columns=list(TRADES_COLUMNS))
