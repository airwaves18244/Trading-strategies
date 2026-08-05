"""Carry / term-structure family engine (WS-D1).

Consumes precomputed frames from ctx.extras. Documented extras keys:
  - "basis_ann":   DataFrame (ts x asset) annualized basis/slope, positive = backwardation
  - "funding_ann": DataFrame (ts x asset) annualized funding rate (crypto perps)
  - "vol_curve":   DataFrame with columns [date, expiry, settle, symbol] (vol futures)
Integration (WS-F) builds these from provider chains; strategies must degrade
gracefully (empty weights) when the key is absent — check with `has_extras`.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def has_extras(ctx, key: str) -> bool:
    df = ctx.extras.get(key)
    return df is not None and len(df) > 0


def annualized_basis(near: pd.DataFrame, far: pd.DataFrame, days_between: float | pd.DataFrame) -> pd.DataFrame:
    """(near/far - 1) * 365/days — positive = backwardation (near above far)."""
    return (near / far - 1.0) * (365.0 / days_between)


def slope_zscore(basis_ann: pd.DataFrame, window: int = 252, min_periods: int = 63) -> pd.DataFrame:
    """Time-series z of each asset's own carry (strictly trailing)."""
    mu = basis_ann.rolling(window, min_periods=min_periods).mean().shift(1)
    sd = basis_ann.rolling(window, min_periods=min_periods).std().shift(1)
    return ((basis_ann - mu) / sd).replace([np.inf, -np.inf], np.nan)


def carry_xs_signal(basis_ann: pd.DataFrame, clamp: float = 2.0) -> pd.DataFrame:
    """Cross-sectional z-score of carry per date, clamped — feed to xs weights."""
    mu = basis_ann.mean(axis=1)
    sd = basis_ann.std(axis=1).replace(0, np.nan)
    z = basis_ann.sub(mu, axis=0).div(sd, axis=0)
    return z.clip(-clamp, clamp)


def carry_ts_signal(basis_ann: pd.DataFrame, hurdle_ann: float = 0.0, clamp: float = 1.0) -> pd.DataFrame:
    """Time-series carry sign/size vs a hurdle: sign(carry - hurdle), scaled."""
    s = np.sign(basis_ann - hurdle_ann) * np.minimum(1.0, (basis_ann - hurdle_ann).abs() / 0.10)
    return pd.DataFrame(s, index=basis_ann.index, columns=basis_ann.columns).clip(-clamp, clamp)


def deseasonalized_slope(basis_ann: pd.DataFrame, window_years: int = 3) -> pd.DataFrame:
    """Subtract each asset's same-calendar-month trailing mean (seasonal carry fix,
    doc 05-02 §3). Strictly trailing: month means exclude the current observation."""
    out = basis_ann.copy()
    months = basis_ann.index.month
    for m in range(1, 13):
        mask = months == m
        sub = basis_ann.loc[mask]
        seasonal_mean = sub.rolling(window_years, min_periods=1).mean().shift(1)
        out.loc[mask] = sub - seasonal_mean
    return out


def vix_style_basis(vol_curve: pd.DataFrame, spot: pd.Series | None = None) -> pd.DataFrame:
    """From a long vol-futures curve table [date, expiry, settle] build per-date
    front/second settle and basis metrics. Returns DataFrame indexed by date with
    columns [vx1, vx2, days1, days2, basis1 (vx1/spot-1 if spot), slope12 (vx2/vx1-1)]."""
    df = vol_curve.copy()
    df["date"] = pd.to_datetime(df["date"], utc=True)
    df["expiry"] = pd.to_datetime(df["expiry"], utc=True)
    df = df[df["expiry"] > df["date"]].sort_values(["date", "expiry"])
    rows = []
    for dt, g in df.groupby("date"):
        g = g.head(2)
        if len(g) < 2:
            continue
        vx1, vx2 = float(g.iloc[0]["settle"]), float(g.iloc[1]["settle"])
        rows.append({
            "date": dt, "vx1": vx1, "vx2": vx2,
            "days1": (g.iloc[0]["expiry"] - dt).days, "days2": (g.iloc[1]["expiry"] - dt).days,
            "slope12": vx2 / vx1 - 1.0 if vx1 > 0 else np.nan,
            "basis1": (vx1 / float(spot.reindex([dt]).iloc[0]) - 1.0)
            if spot is not None and dt in spot.index and np.isfinite(spot.reindex([dt]).iloc[0]) else np.nan,
        })
    return pd.DataFrame(rows).set_index("date").sort_index()
