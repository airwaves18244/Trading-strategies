"""Time-series (per-instrument) signal engine (WS-D1 family engine #2).

Produces a bounded signal in ``[-clamp, +clamp]`` for every (bar, symbol) by
averaging several trailing lookbacks, then converts it to weights with
per-asset volatility targeting and optional asset-class risk buckets.

Corpus references
-----------------
``strategies/02-momentum/02-time-series-momentum.md`` §3 (multi-lookback sign
ensemble, per-asset inverse-vol sizing), ``strategies/03-trend-following/01-…``
§3 (EWMA crossover ensemble à la AHL/Baltas: pairs (8,24), (16,48), (32,96)
normalised by trailing price vol), ``strategies/03-…/02`` (Donchian channel
position). ``strategies/06-volatility/04-…`` §3 warns that trend books already
embed vol targeting — do not double-apply :class:`~qbt.strategy.lib.overlay.VolTargetOverlay`
on top of :func:`to_weights` output without thinking.

Used by: ts_momentum, dual_momentum, managed_futures_trend, trend_plus_carry,
overnight_intraday, turn_of_month.

Look-ahead policy
-----------------
Causal by construction. The *level* at ``t`` (price, return) is allowed; every
rolling statistic used as a **reference level or scale** (channel high/low,
normalising std) is computed over a window ending at ``t-1`` via ``.shift(1)``,
so a bar can never define its own normaliser. The runner applies the execution
lag on top.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd

__all__ = [
    "ts_ensemble",
    "to_weights",
    "trailing_vol",
    "SIGNAL_KINDS",
    "DEFAULT_EWMA_PAIRS",
]

SIGNAL_KINDS: tuple[str, ...] = ("return_sign", "ewma_xover", "channel")

#: AHL/Baltas-style fast/slow spans (``strategies/03-trend-following/01`` §3)
DEFAULT_EWMA_PAIRS: tuple[tuple[int, int], ...] = ((8, 24), (16, 48), (32, 96))

_EPS = 1e-12


def _as_price(frame: pd.DataFrame | pd.Series, is_returns: bool) -> pd.DataFrame:
    """Accept either a price/TR index or simple returns; return a price index."""
    df = frame.to_frame() if isinstance(frame, pd.Series) else frame
    df = df.astype(float)
    if not is_returns:
        return df
    return (1.0 + df.fillna(0.0)).cumprod()


def trailing_vol(
    returns: pd.DataFrame,
    window: int = 63,
    min_periods: int | None = None,
    lag: int = 1,
    annualize: float | None = None,
) -> pd.DataFrame:
    """Trailing per-asset return volatility, strictly lagged by ``lag`` bars.

    ``annualize`` = bars per year (e.g. 252) to get annualised vol; ``None``
    leaves it per-bar. Used as the ``vol`` argument of :func:`to_weights` and of
    :func:`~qbt.strategy.lib.xs_rank.cross_sectional_weights`.
    """
    mp = min_periods if min_periods is not None else max(5, window // 3)
    v = returns.astype(float).rolling(window, min_periods=mp).std(ddof=0)
    if lag:
        v = v.shift(lag)
    if annualize:
        v = v * float(np.sqrt(annualize))
    return v


def ts_ensemble(
    close_or_ret: pd.DataFrame | pd.Series,
    lookbacks: Sequence[int] = (21, 63, 252),
    kind: str = "return_sign",
    clamp: float = 1.0,
    is_returns: bool = False,
    ewma_pairs: Sequence[tuple[int, int]] = DEFAULT_EWMA_PAIRS,
    vol_window: int = 63,
    norm_window: int = 252,
    min_periods_frac: float = 0.5,
) -> pd.DataFrame:
    """Multi-lookback trend signal in ``[-clamp, +clamp]``.

    Parameters
    ----------
    close_or_ret:
        price / total-return index frame (default) or simple returns when
        ``is_returns=True``. A Series is accepted and returned as a 1-column
        frame.
    lookbacks:
        bars per lookback. ``(21, 63, 252)`` ≈ 1m / 3m / 12m — the standard
        TSMOM ensemble; averaging kills the single-lookback timing luck that
        ``strategies/02-momentum/02`` §3 flags.
        Used by ``return_sign`` and ``channel``; ignored by ``ewma_xover``
        (which uses ``ewma_pairs``).
    kind:
        ``"return_sign"``  — mean of ``sign(P_t / P_{t-L} - 1)`` over lookbacks.
                             Output lives on the grid {-1, …, +1}.
        ``"ewma_xover"``   — mean over ``ewma_pairs`` of
                             ``(EWMA_fast - EWMA_slow) / trailing_std(P)``,
                             each re-standardised by its own trailing std so the
                             three speeds contribute comparable risk.
        ``"channel"``      — mean over lookbacks of the Donchian position
                             ``2*(P_t - lo)/(hi - lo) - 1`` where hi/lo are the
                             trailing extremes over the window ending at t-1.
    clamp:
        output is clipped to ``[-clamp, clamp]``. ``clamp=1.0`` keeps the signal
        interpretable as "fraction of full risk, signed".
    vol_window, norm_window:
        ``ewma_xover`` internals: price-difference scaler window and the
        self-standardisation window.
    min_periods_frac:
        fraction of a window that must be populated before a value is emitted —
        NaN robustness for short histories / newly listed names.

    Returns
    -------
    DataFrame, same index/columns as the input, NaN where no lookback had
    enough history, otherwise within ``[-clamp, clamp]``.
    """
    if kind not in SIGNAL_KINDS:
        raise ValueError(f"kind must be one of {SIGNAL_KINDS}, got {kind!r}")
    if clamp <= 0:
        raise ValueError(f"clamp must be positive, got {clamp}")
    px = _as_price(close_or_ret, is_returns)

    if kind == "return_sign":
        parts = [_sign_signal(px, int(L)) for L in lookbacks]
    elif kind == "channel":
        parts = [_channel_signal(px, int(L), min_periods_frac) for L in lookbacks]
    else:
        parts = [
            _xover_signal(px, int(f), int(s), vol_window, norm_window, min_periods_frac)
            for f, s in ewma_pairs
        ]
    if not parts:
        raise ValueError("no lookbacks given")

    # NaN-robust mean across lookbacks without reshaping (a lookback that has
    # not warmed up yet simply does not vote).
    arr = np.stack([p.reindex(index=px.index, columns=px.columns).to_numpy(dtype=float)
                    for p in parts])
    with np.errstate(invalid="ignore"):
        avg = np.where(np.all(np.isnan(arr), axis=0), np.nan, np.nanmean(arr, axis=0))
    sig = pd.DataFrame(avg, index=px.index, columns=px.columns)
    return sig.clip(-float(clamp), float(clamp))


def _sign_signal(px: pd.DataFrame, lookback: int) -> pd.DataFrame:
    prev = px.shift(lookback)
    r = (px / prev.replace(0.0, np.nan)) - 1.0
    return np.sign(r).where(r.notna())


def _channel_signal(px: pd.DataFrame, lookback: int, min_frac: float) -> pd.DataFrame:
    mp = max(2, int(lookback * min_frac))
    hi = px.rolling(lookback, min_periods=mp).max().shift(1)
    lo = px.rolling(lookback, min_periods=mp).min().shift(1)
    rng = (hi - lo)
    pos = 2.0 * (px - lo) / rng.where(rng.abs() > _EPS) - 1.0
    # price outside the trailing channel is a breakout: saturate rather than blow up
    return pos.clip(-1.0, 1.0).where(hi.notna() & lo.notna())


def _xover_signal(
    px: pd.DataFrame, fast: int, slow: int, vol_window: int, norm_window: int, min_frac: float
) -> pd.DataFrame:
    raw = px.ewm(span=fast, min_periods=fast).mean() - px.ewm(span=slow, min_periods=slow).mean()
    scale = px.rolling(vol_window, min_periods=max(3, int(vol_window * min_frac))).std(ddof=0).shift(1)
    y = raw / scale.where(scale.abs() > _EPS)
    ynorm = y.rolling(norm_window, min_periods=max(10, int(norm_window * min_frac))).std(ddof=0).shift(1)
    out = y / ynorm.where(ynorm.abs() > _EPS)
    return out.replace([np.inf, -np.inf], np.nan)


def to_weights(
    signal: pd.DataFrame,
    vol: pd.DataFrame | None = None,
    per_asset_target: float = 0.10,
    group_map: Mapping[str, str] | None = None,
    group_risk_caps: Mapping[str, float] | None = None,
    ann_factor: float = 252.0,
    max_asset_weight: float = 1.0,
    max_gross: float | None = None,
    universe_mask: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Signal → target weights with per-asset vol targeting and group caps.

    ``w_i,t = signal_i,t * per_asset_target / annualised_vol_i,t``

    i.e. each instrument is sized so a *full* signal (|s| = 1) runs at
    ``per_asset_target`` annualised vol — the standard managed-futures sizing of
    ``strategies/03-trend-following/01`` §3. With ``vol=None`` the signal is used
    as the weight directly (already-normalised books).

    Parameters
    ----------
    vol:
        per-bar (not annualised) trailing return volatility; use
        :func:`trailing_vol`. Must be causal — this function does not shift it.
    per_asset_target:
        annualised vol budget per instrument at full signal.
    ann_factor:
        bars per year, ``ctx.ann_factor``.
    max_asset_weight:
        hard clip on |w| per instrument, protects against a near-zero vol
        estimate turning into 40x leverage.
    group_map / group_risk_caps:
        ``{symbol: group}`` and ``{group: max_gross_for_that_group}``; a group
        over its cap is scaled down pro-rata on that bar. The commodity carry
        doc (``strategies/05-carry/02`` §3) asks for "sector risk caps (<= 40%)".
    max_gross:
        optional cap on total gross exposure per bar (scaled pro-rata).
    universe_mask:
        optional bool frame; non-members are forced to 0.

    Returns
    -------
    Weights DataFrame, no NaNs.
    """
    sig = signal.astype(float)
    if vol is None:
        w = sig.copy()
    else:
        v = vol.reindex(index=sig.index, columns=sig.columns).astype(float)
        ann_vol = v * float(np.sqrt(ann_factor))
        w = sig * (float(per_asset_target) / ann_vol.where(ann_vol > _EPS))
    w = w.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    w = w.clip(-float(max_asset_weight), float(max_asset_weight))

    if universe_mask is not None:
        m = universe_mask.reindex(index=w.index, columns=w.columns).fillna(False).astype(bool)
        w = w.where(m, 0.0)

    if group_map and group_risk_caps:
        for group, cap in group_risk_caps.items():
            cols = [c for c in w.columns if str(group_map.get(c, "__none__")) == str(group)]
            if not cols:
                continue
            g = w[cols].abs().sum(axis=1)
            factor = (float(cap) / g.where(g > _EPS)).clip(upper=1.0).fillna(1.0)
            w[cols] = w[cols].mul(factor, axis=0)

    if max_gross is not None:
        g = w.abs().sum(axis=1)
        factor = (float(max_gross) / g.where(g > _EPS)).clip(upper=1.0).fillna(1.0)
        w = w.mul(factor, axis=0)
    return w
