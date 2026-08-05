"""Cross-sectional ranking engine (WS-D1 family engine #1).

Turns a *signal frame* (index = calendar, columns = symbols) into a *weights
frame* by ranking names inside the point-in-time universe on rebalance dates and
holding the resulting book constant until the next rebalance.

Corpus reference — ``strategies/02-momentum/01-cross-sectional-equity-momentum.md`` §3:

    "Signal: total return from t-12 months to t-1 month (skip the most recent
     month). Portfolio: rank; long top decile, short bottom decile (long-only:
     overweight top quintile/decile) ... Rebalance: monthly ...
     Sector-neutral variant: rank within sectors."

Used by (registry map, docs/architecture.md): xs_equity_momentum, residual_momentum,
industry_factor_momentum, week52_high_momentum, commodity_xs_momentum,
short_term_reversal, equity_value_quality, cross_asset_value, low_vol_bab,
fundamental_seasonality, stat_arb_residual (residual leg).

Look-ahead policy
-----------------
Every function here is *causal*: the value produced for bar ``t`` never reads a
row later than ``t``, so ``generate(full)[:t] == generate(ctx.slice(t))`` holds
(the ``assert_no_lookahead`` harness). Weights on a rebalance date ``t`` are the
decision taken with information available at the close of ``t``; the runner adds
``shift_for_execution(lag)`` on top, so the book is actually traded at ``t+lag``.
Statistics used as *scales* (``vol`` for inverse-vol weighting) must be supplied
already trailing by the caller — see :func:`skip_month_return` for the pattern.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd

__all__ = [
    "cross_sectional_weights",
    "zscore_xs",
    "rank_xs",
    "skip_month_return",
    "WEIGHTING_SCHEMES",
]

#: allowed values for the ``weighting`` argument of :func:`cross_sectional_weights`
WEIGHTING_SCHEMES: tuple[str, ...] = ("equal", "inverse_vol", "signal")

_EPS = 1e-12


# --------------------------------------------------------------------------- #
# signal helpers                                                              #
# --------------------------------------------------------------------------- #
def zscore_xs(
    signal: pd.DataFrame,
    universe_mask: pd.DataFrame | None = None,
    winsor: float | None = 3.0,
    min_names: int = 3,
) -> pd.DataFrame:
    """Row-wise (cross-sectional) z-score.

    Parameters
    ----------
    signal:
        index = calendar, columns = symbols. NaNs are ignored (they stay NaN).
    universe_mask:
        optional bool frame; entries that are False are excluded from the mean /
        std *and* returned as NaN.
    winsor:
        clip the result to +/- this many sigmas (``None`` disables). Winsorising
        after standardising is the cheap way to stop one broken print from
        eating the whole book.
    min_names:
        rows with fewer valid names than this are returned all-NaN.

    Returns
    -------
    DataFrame of the same shape, mean 0 / std 1 across each row.
    """
    x = signal.astype(float)
    if universe_mask is not None:
        mask = universe_mask.reindex(index=x.index, columns=x.columns).fillna(False)
        x = x.where(mask.astype(bool))
    n = x.notna().sum(axis=1)
    mu = x.mean(axis=1, skipna=True)
    sd = x.std(axis=1, skipna=True, ddof=0)
    z = x.sub(mu, axis=0).div(sd.replace(0.0, np.nan), axis=0)
    z = z.where(n.ge(min_names), np.nan)
    if winsor is not None:
        z = z.clip(-float(winsor), float(winsor))
    return z


def rank_xs(
    signal: pd.DataFrame,
    universe_mask: pd.DataFrame | None = None,
    pct: bool = True,
) -> pd.DataFrame:
    """Row-wise rank (1 = smallest). ``pct=True`` maps to (0, 1]."""
    x = signal.astype(float)
    if universe_mask is not None:
        mask = universe_mask.reindex(index=x.index, columns=x.columns).fillna(False)
        x = x.where(mask.astype(bool))
    return x.rank(axis=1, pct=pct, na_option="keep")


def skip_month_return(
    tr: pd.DataFrame,
    formation: int = 12,
    skip: int = 1,
    bars_per_month: int = 21,
) -> pd.DataFrame:
    """Momentum formation return over t-``formation`` months .. t-``skip`` months.

    ``skip_month_return(tr, 12, 1)`` is the canonical 12-1 momentum signal: the
    total return from 12 months ago to 1 month ago, deliberately *excluding* the
    most recent month because it reverses
    (``strategies/02-momentum/01-…`` §3 and ``strategies/04-…/01`` short-term
    reversal).

    Parameters
    ----------
    tr:
        total-return index frame (``ctx.total_return``), NOT simple returns.
    formation, skip:
        months. ``skip=0`` includes the most recent month.
    bars_per_month:
        calendar granularity — 21 trading bars per month for daily data.

    Returns
    -------
    DataFrame of simple returns; NaN until ``formation*bars_per_month`` bars of
    history exist. Strictly trailing: with ``skip>=1`` the value at ``t`` only
    uses prices up to ``t - skip*bars_per_month``.
    """
    if formation <= skip:
        raise ValueError(f"formation ({formation}) must exceed skip ({skip})")
    px = tr.astype(float)
    near = px.shift(skip * bars_per_month)
    far = px.shift(formation * bars_per_month)
    return (near / far.replace(0.0, np.nan)) - 1.0


# --------------------------------------------------------------------------- #
# the engine                                                                  #
# --------------------------------------------------------------------------- #
def cross_sectional_weights(
    signal: pd.DataFrame,
    universe_mask: pd.DataFrame,
    top_frac: float = 0.1,
    bottom_frac: float = 0.1,
    long_only: bool = True,
    sector_map: Mapping[str, str] | None = None,
    sector_neutral: bool = False,
    weighting: str = "equal",
    vol: pd.DataFrame | None = None,
    rebalance_dates: pd.DatetimeIndex | Sequence[pd.Timestamp] | None = None,
    min_names: int = 5,
    gross: float = 1.0,
    drop_when_out_of_universe: bool = True,
) -> pd.DataFrame:
    """Rank → fractile → weights, held between rebalances.

    Algorithm, per rebalance date ``t``
      1. the *pool* = symbols with a finite ``signal`` value AND
         ``universe_mask`` True at ``t``;
      2. if ``sector_neutral`` the pool is split into one sub-pool per sector
         (``sector_map``) and steps 3-4 run inside each sub-pool — this is the
         "rank within sectors" variant of §3, it removes the accidental sector
         bet without removing the name-level bet;
      3. a sub-pool with fewer than ``min_names`` valid names is skipped
         entirely (no half-baked deciles);
      4. the top ``round(n*top_frac)`` names (at least 1) go long; the bottom
         ``round(n*bottom_frac)`` go short — zeroed when ``long_only``;
      5. raw leg weights come from ``weighting`` and are normalised so that the
         long leg sums to ``gross`` (long-only) or ``gross/2`` and the short leg
         to ``-gross/2`` (long/short → gross exposure ``gross``).

    Between rebalance dates the book is held constant (forward fill), which is
    what "rebalance: monthly" means operationally. Rows before the first
    rebalance date are 0.

    Parameters
    ----------
    signal:
        higher = more attractive (long side). Must already be causal.
    universe_mask:
        bool frame, PIT membership AND tradability (``ctx.universe_mask``).
    top_frac, bottom_frac:
        fractile sizes, e.g. 0.1 = decile (§3 "long top decile, short bottom
        decile"), 0.2 = quintile, 0.33 = tercile (carry docs).
    long_only:
        default True for equities — MOEX post-2022 shorting is a fixed risk
        decision (docs/architecture.md "Key risk decisions" #2). When True the
        short leg is computed then discarded, so switching the flag does not
        change which names are long.
    sector_map:
        ``{symbol: sector}``; symbols missing from the map land in sector
        ``"__none__"``.
    sector_neutral:
        rank inside sectors instead of across the whole universe.
    weighting:
        ``"equal"``     — 1/n inside each leg;
        ``"inverse_vol"`` — proportional to 1/``vol`` (risk parity inside the
        leg; ``vol`` must be a *trailing* volatility frame, e.g.
        ``ctx.ret().rolling(60).std().shift(1)``);
        ``"signal"``    — proportional to |cross-sectional z-score| (conviction
        weighting). Value-weighting is not offered here because market cap is
        not part of the frozen DataContext; pass it via ``vol``-style frames in
        a bespoke strategy if needed.
    vol:
        required for ``weighting="inverse_vol"``; ignored otherwise.
    rebalance_dates:
        typically ``ctx.rebalance_dates("ME")``. ``None`` = rebalance every bar.
        Dates outside ``signal.index`` are ignored.
    min_names:
        minimum valid names in a pool (whole universe, or one sector when
        ``sector_neutral``) before it is traded.
    gross:
        target gross exposure of the book on a rebalance date.
    drop_when_out_of_universe:
        after the forward fill, zero any held name whose ``universe_mask`` went
        False (delisting / halt). Gross then drifts below target until the next
        rebalance rather than silently re-levering.

    Returns
    -------
    DataFrame, index = ``signal.index``, columns = ``signal.columns``, float,
    no NaNs.

    Complexity: O(n_rebalances * n_symbols log n_symbols).
    """
    if weighting not in WEIGHTING_SCHEMES:
        raise ValueError(f"weighting must be one of {WEIGHTING_SCHEMES}, got {weighting!r}")
    if weighting == "inverse_vol" and vol is None:
        raise ValueError("weighting='inverse_vol' requires a `vol` frame")
    if not 0.0 < top_frac <= 1.0:
        raise ValueError(f"top_frac must be in (0, 1], got {top_frac}")
    if not 0.0 <= bottom_frac <= 1.0:
        raise ValueError(f"bottom_frac must be in [0, 1], got {bottom_frac}")

    sig = signal.astype(float)
    cols = list(sig.columns)
    mask = (
        universe_mask.reindex(index=sig.index, columns=cols)
        .fillna(False)
        .astype(bool)
    )
    volf = None
    if vol is not None:
        volf = vol.reindex(index=sig.index, columns=cols).astype(float)

    if rebalance_dates is None:
        rb = sig.index
    else:
        rb = pd.DatetimeIndex(rebalance_dates)
        rb = sig.index.intersection(rb)

    zs = zscore_xs(sig, mask, winsor=3.0, min_names=1) if weighting == "signal" else None

    out = pd.DataFrame(np.nan, index=sig.index, columns=cols, dtype=float)
    for t in rb:
        row = _row_weights(
            sig_row=sig.loc[t],
            mask_row=mask.loc[t],
            vol_row=None if volf is None else volf.loc[t],
            z_row=None if zs is None else zs.loc[t],
            top_frac=top_frac,
            bottom_frac=bottom_frac,
            long_only=long_only,
            sector_map=sector_map,
            sector_neutral=sector_neutral,
            weighting=weighting,
            min_names=min_names,
            gross=gross,
        )
        out.loc[t] = row

    out = out.ffill().fillna(0.0)
    if drop_when_out_of_universe:
        out = out.where(mask, 0.0)
    return out


def _row_weights(
    sig_row: pd.Series,
    mask_row: pd.Series,
    vol_row: pd.Series | None,
    z_row: pd.Series | None,
    top_frac: float,
    bottom_frac: float,
    long_only: bool,
    sector_map: Mapping[str, str] | None,
    sector_neutral: bool,
    weighting: str,
    min_names: int,
    gross: float,
) -> pd.Series:
    """One rebalance date. Returns a weight Series (zeros where not selected)."""
    w = pd.Series(0.0, index=sig_row.index, dtype=float)
    valid = sig_row.notna() & mask_row.astype(bool)
    if weighting == "inverse_vol" and vol_row is not None:
        valid &= vol_row.notna() & (vol_row > 0)
    pool_all = list(sig_row.index[valid])
    if not pool_all:
        return w

    if sector_neutral and sector_map is not None:
        buckets: dict[str, list[str]] = {}
        for s in pool_all:
            buckets.setdefault(str(sector_map.get(s, "__none__")), []).append(s)
        pools = list(buckets.values())
    else:
        pools = [pool_all]

    longs: list[str] = []
    shorts: list[str] = []
    for pool in pools:
        n = len(pool)
        if n < min_names:
            continue
        n_top = max(1, int(round(n * top_frac)))
        n_bot = 0 if long_only else max(1, int(round(n * bottom_frac)))
        if n_top + n_bot > n:                      # tiny pool: longs win the tie
            n_top = min(n_top, n)
            n_bot = max(0, n - n_top)
        # deterministic ordering: sort by (-signal, symbol) so ties never depend
        # on column order or on numpy's introsort.
        ordered = sorted(pool, key=lambda s: (-float(sig_row[s]), str(s)))
        longs.extend(ordered[:n_top])
        if n_bot:
            shorts.extend(ordered[len(ordered) - n_bot:])

    if not longs and not shorts:
        return w

    two_sided = bool(shorts)
    long_budget = gross / 2.0 if two_sided else gross
    short_budget = gross / 2.0

    for names, budget, sign in ((longs, long_budget, 1.0), (shorts, short_budget, -1.0)):
        if not names:
            continue
        raw = _raw_leg_weights(names, sig_row, vol_row, z_row, weighting)
        total = float(raw.sum())
        if total <= _EPS:                            # degenerate → equal weight
            raw = pd.Series(1.0 / len(names), index=names, dtype=float)
            total = 1.0
        scaled = raw / total * budget * sign
        for s, v in scaled.items():
            w[s] += float(v)
    return w


def _raw_leg_weights(
    names: list[str],
    sig_row: pd.Series,
    vol_row: pd.Series | None,
    z_row: pd.Series | None,
    weighting: str,
) -> pd.Series:
    """Positive, un-normalised weights inside one leg."""
    if weighting == "equal":
        return pd.Series(1.0, index=names, dtype=float)
    if weighting == "inverse_vol":
        v = vol_row.reindex(names).astype(float)
        v = v.where(v > 0)
        raw = 1.0 / v
        return raw.fillna(0.0)
    # "signal": conviction weighting on |z|, floored so a zero-z name still trades
    z = z_row.reindex(names).astype(float).abs() if z_row is not None else None
    if z is None:
        return pd.Series(1.0, index=names, dtype=float)
    return z.fillna(0.0).clip(lower=1e-6)
