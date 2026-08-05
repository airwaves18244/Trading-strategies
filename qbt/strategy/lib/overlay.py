"""Overlay implementations + composition (WS-D1).

VolTargetOverlay implements the Overlay protocol (qbt/strategy/base.py); it is
self-contained (own lagged EWMA — no import from qbt.engine.risk, which is a
parallel workstream).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from qbt.engine.context import DataContext


class VolTargetOverlay:
    """Scale the whole weights row by target / realized portfolio vol (lagged).

    Doc 06-volatility/04 §3: exposure_t = clamp(target/σ̂_{t-1}, floor, cap),
    σ̂ from EWMA of the *strategy's own* weighted returns; band rebalancing.
    """

    def __init__(self, target: float = 0.10, halflife: int = 20,
                 cap: float = 2.0, floor: float = 0.3, band: float = 0.15,
                 ann_factor: float = 252.0):
        self.name = f"vol_target({target:.0%})"
        self.target, self.halflife = target, halflife
        self.cap, self.floor, self.band = cap, floor, band
        self.ann_factor = ann_factor

    def transform(self, weights: pd.DataFrame, ctx: DataContext) -> pd.DataFrame:
        r = ctx.ret().reindex_like(weights).fillna(0.0)
        strat_ret = (weights.shift(1).fillna(0.0) * r).sum(axis=1)
        var = strat_ret.pow(2).ewm(halflife=self.halflife,
                                   min_periods=max(5, self.halflife // 2)).mean()
        sigma = np.sqrt(var * self.ann_factor).shift(1)  # strictly lagged
        raw = (self.target / sigma).clip(lower=self.floor, upper=self.cap)
        # band rebalancing: only move the scalar when it drifts > band
        scale = raw.copy()
        last = 1.0
        vals = raw.to_numpy()
        out = np.empty_like(vals)
        for i, v in enumerate(vals):
            if not np.isfinite(v):
                out[i] = last
                continue
            if abs(v - last) / max(last, 1e-12) > self.band:
                last = v
            out[i] = last
        scale = pd.Series(out, index=raw.index)
        return weights.mul(scale, axis=0)


def compose(weights_list: list[pd.DataFrame], risk_weights: list[float] | None = None,
            gross: float | None = None) -> pd.DataFrame:
    """Weighted sum of sleeve weight matrices (aligned union of index/columns).

    risk_weights default equal. If `gross` given, rescale so average gross matches."""
    if not weights_list:
        raise ValueError("empty weights_list")
    rw = risk_weights or [1.0 / len(weights_list)] * len(weights_list)
    if len(rw) != len(weights_list):
        raise ValueError("risk_weights length mismatch")
    idx = weights_list[0].index
    cols: set[str] = set()
    for w in weights_list:
        idx = idx.union(w.index)
        cols |= set(w.columns)
    total = pd.DataFrame(0.0, index=idx.sort_values(), columns=sorted(cols))
    for w, k in zip(weights_list, rw):
        total = total.add(w.reindex(index=total.index, columns=total.columns).fillna(0.0) * k,
                          fill_value=0.0)
    if gross:
        g = total.abs().sum(axis=1).replace(0, np.nan).mean()
        if np.isfinite(g) and g > 0:
            total *= gross / g
    return total
