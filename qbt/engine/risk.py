"""Risk pipeline primitives (WS-C).

Every function here is a *pure* frame transform. The single rule the whole
engine rests on: **nothing may use information from the bar it is applied to**.
`ex_ante_vol` therefore returns an already-shifted frame, and
`shift_for_execution` is the ONE choke point where signal-time becomes
execution-time.

Pipeline order used by the runner::

    ex_ante_vol -> inverse_vol_weights -> vol_target -> apply_caps -> shift_for_execution
"""
from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import pandas as pd

__all__ = [
    "ex_ante_vol", "inverse_vol_weights", "vol_target", "vol_target_scalar",
    "apply_caps", "shift_for_execution",
]

_EPS = 1e-12


def _as_frame(x: pd.Series | pd.DataFrame, name: str = "value") -> pd.DataFrame:
    if isinstance(x, pd.Series):
        return x.to_frame(x.name if x.name is not None else name)
    return x


def ex_ante_vol(
    rets: pd.DataFrame | pd.Series,
    method: str = "ewma",
    halflife: float = 20,
    min_periods: int = 20,
    ann: float = 252,
) -> pd.DataFrame:
    """Annualised volatility estimate, **already shifted**.

    The value at row ``t`` is computed from returns up to and including ``t-1``,
    so it can be multiplied into a weight that is itself applied at ``t``
    without look-ahead.

    method:
        ``"ewma"``   RiskMetrics: sqrt(EWMA(r^2)) — no mean subtraction, so a
                     deterministic +v/-v stream yields exactly ``v`` (analytic
                     anchor for the vol-target tests).
        ``"ewma_std"`` EWMA standard deviation (mean subtracted).
        ``"rolling"``  rolling standard deviation with ``window = halflife``.
    """
    df = _as_frame(rets).astype(float)
    hl = float(halflife)
    mp = int(min_periods)
    if method == "ewma":
        var = (df ** 2).ewm(halflife=hl, min_periods=mp, adjust=True, ignore_na=False).mean()
        vol = np.sqrt(var)
    elif method == "ewma_std":
        vol = df.ewm(halflife=hl, min_periods=mp, adjust=True, ignore_na=False).std()
    elif method in ("rolling", "std"):
        window = max(int(round(hl)), 2)
        vol = df.rolling(window, min_periods=mp).std()
    else:
        raise ValueError(f"unknown ex_ante_vol method {method!r}; "
                         "use 'ewma', 'ewma_std' or 'rolling'")
    out = vol * float(np.sqrt(ann))
    return out.shift(1)


def inverse_vol_weights(
    signal: pd.DataFrame | pd.Series,
    vol: pd.DataFrame | pd.Series,
    target_vol_per_asset: float,
) -> pd.DataFrame:
    """Scale a (typically [-1, 1]) signal so each asset carries the same ex-ante vol.

    ``w = signal * target_vol_per_asset / vol``. Assets with a missing or
    non-positive vol estimate get weight 0 (no estimate => no position).
    """
    sig = _as_frame(signal).astype(float)
    v = _as_frame(vol).astype(float).reindex(index=sig.index, columns=sig.columns)
    v = v.where(v > _EPS)
    out = sig * (float(target_vol_per_asset) / v)
    return out.replace([np.inf, -np.inf], np.nan).fillna(0.0)


def _portfolio_vol(
    weights: pd.DataFrame,
    asset_vol_or_returns: pd.DataFrame | pd.Series,
    halflife: float,
    min_periods: int,
    ann: float,
    method: str,
) -> pd.Series:
    """Ex-ante portfolio vol, strictly lagged.

    ``asset_vol_or_returns`` is auto-detected: a frame containing negative
    values is treated as *returns* (exact route — the portfolio return series is
    formed with the current weights and passed through ``ex_ante_vol``); a
    non-negative frame is treated as a per-asset *vol* frame and combined under
    a diagonal-covariance approximation, ``sqrt(sum((w*vol)^2))``.
    """
    src = _as_frame(asset_vol_or_returns).astype(float)
    src = src.reindex(index=weights.index, columns=weights.columns)
    looks_like_returns = bool((src < -_EPS).any().any())
    if looks_like_returns:
        port_ret = (weights.fillna(0.0) * src.fillna(0.0)).sum(axis=1)
        # a bar with no position contributes a genuine 0 return
        pv = ex_ante_vol(port_ret, method=method, halflife=halflife,
                         min_periods=min_periods, ann=ann).iloc[:, 0]
        return pv
    contrib = (weights.fillna(0.0) * src) ** 2
    return np.sqrt(contrib.sum(axis=1, min_count=1))


def vol_target_scalar(
    weights: pd.DataFrame,
    asset_vol_or_returns: pd.DataFrame | pd.Series,
    target: float = 0.10,
    cap: float = 2.0,
    floor: float = 0.3,
    band: float = 0.15,
    halflife: float = 20,
    min_periods: int = 20,
    ann: float = 252,
    method: str = "ewma",
) -> pd.Series:
    """The portfolio-level scalar applied by :func:`vol_target` (exposed for tests)."""
    w = _as_frame(weights).astype(float)
    pv = _portfolio_vol(w, asset_vol_or_returns, halflife, min_periods, ann, method)
    raw = pd.Series(np.where(pv.to_numpy() > _EPS, float(target) / pv.to_numpy(), np.nan),
                    index=w.index)
    raw = raw.clip(lower=float(floor), upper=float(cap))

    b = float(band)
    vals = raw.to_numpy()
    out = np.full(len(vals), np.nan)
    current = np.nan
    for i, v in enumerate(vals):
        if not np.isfinite(v):
            out[i] = current if np.isfinite(current) else np.nan
            continue
        if not np.isfinite(current):
            current = v
        elif b <= 0.0:
            current = v
        elif abs(v - current) > b * abs(current):
            current = v
        out[i] = current
    return pd.Series(out, index=w.index, name="vol_target_scalar")


def vol_target(
    weights: pd.DataFrame,
    asset_vol_or_returns: pd.DataFrame | pd.Series,
    target: float = 0.10,
    cap: float = 2.0,
    floor: float = 0.3,
    band: float = 0.15,
    halflife: float = 20,
    min_periods: int = 20,
    ann: float = 252,
    method: str = "ewma",
) -> pd.DataFrame:
    """Portfolio-level vol targeting with a rebalance band.

    The scalar is ``target / ex-ante portfolio vol`` clipped to ``[floor, cap]``,
    but it is only *moved* when the fresh reading drifts more than ``band``
    (relative) from the scalar currently in force — otherwise the overlay would
    trade every single day for nothing.

    Bars with no volatility estimate yet get weight 0 (flat), never an
    unscaled position.
    """
    w = _as_frame(weights).astype(float)
    scalar = vol_target_scalar(
        w, asset_vol_or_returns, target=target, cap=cap, floor=floor, band=band,
        halflife=halflife, min_periods=min_periods, ann=ann, method=method,
    )
    return w.mul(scalar.fillna(0.0), axis=0)


def apply_caps(
    weights: pd.DataFrame,
    max_per_instrument: float | None = 0.10,
    max_gross: float | None = 2.0,
    group_map: Mapping[str, str] | None = None,
    max_per_group: float | None = 0.40,
) -> pd.DataFrame:
    """Clip per-instrument, then scale group gross, then scale total gross.

    All scaling is multiplicative and therefore **direction preserving** — signs
    and relative sizes inside a group survive; only magnitude is reduced.
    Pass ``None`` to disable any individual cap.
    """
    w = _as_frame(weights).astype(float).fillna(0.0)
    w = w.replace([np.inf, -np.inf], 0.0)

    if max_per_instrument is not None:
        m = abs(float(max_per_instrument))
        w = w.clip(lower=-m, upper=m)

    if group_map is not None and max_per_group is not None:
        gmax = abs(float(max_per_group))
        groups: dict[str, list[str]] = {}
        for col in w.columns:
            groups.setdefault(str(group_map.get(col, "__ungrouped__")), []).append(col)
        for g, cols in groups.items():
            if g == "__ungrouped__":
                continue
            gross = w[cols].abs().sum(axis=1)
            factor = pd.Series(1.0, index=w.index)
            hot = gross > gmax + _EPS
            factor[hot] = gmax / gross[hot]
            w[cols] = w[cols].mul(factor, axis=0)

    if max_gross is not None:
        gmax = abs(float(max_gross))
        gross = w.abs().sum(axis=1)
        factor = pd.Series(1.0, index=w.index)
        hot = gross > gmax + _EPS
        factor[hot] = gmax / gross[hot]
        w = w.mul(factor, axis=0)

    return w


def shift_for_execution(weights: pd.DataFrame, lag: int = 1) -> pd.DataFrame:
    """THE execution-lag choke point.

    A weight computed from information up to bar ``t`` becomes the position held
    over bar ``t + lag``. ``lag=0`` means same-bar execution (only legitimate
    for signals built from that bar's *open*); the lag canary exists to prove
    the difference is real. Missing weights mean "no position", i.e. 0.
    """
    w = _as_frame(weights).astype(float)
    lag = int(lag)
    if lag < 0:
        raise ValueError(f"execution lag must be >= 0, got {lag}")
    out = w.shift(lag) if lag else w.copy()
    return out.replace([np.inf, -np.inf], np.nan).fillna(0.0)
