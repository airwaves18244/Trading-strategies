"""Pair / spread state machine (WS-D1 family engine #3).

Formation window → hedge ratio → rolling spread z-score → a per-pair state
machine (entry / exit / divergence stop / time stop / half-life filter) →
beta-weighted legs expressed as portfolio weights.

Corpus reference — ``strategies/01-arbitrage-relative-value/01-pairs-trading.md`` §3:

    "Spread: s_t = ln P1_t - beta * ln P2_t. Trade z-score of s on a rolling
     window ~= 3-5 half-lives. Entry |z| > 2, exit z ~= 0, hard stop |z| > 3.5-4
     or re-test failure ... Keep pairs with spread half-life (from AR(1)/OU fit)
     between ~5 and ~40 trading days — too short is untradeable noise, too long
     ties up capital ... beta-weighted legs (not equal dollar)."

Used by: pairs_trading, stat_arb_residual, etf_nav_arbitrage,
convertible_arbitrage, dispersion, cross_exchange_arb.

Look-ahead policy
-----------------
The hedge ratio beta and the spread's mean/std are estimated on windows that end
at ``t-1``; only the *current* spread level enters the z-score at ``t``. Position
changes are recorded on the bar whose information triggered them; the runner adds
the execution lag. Refits happen on a fixed bar calendar, never "when it would
have helped".

Complexity
----------
``pairs_weights`` is O(n_pairs * n_bars) for the state machine plus
O(n_pairs * n_refits * formation) for the OLS refits — a loop, deliberately:
the state machine is path dependent and ``Strategy.output == "weights"`` does not
imply vectorised (see ``qbt/strategy/base.py``). 20 pairs x 2500 bars runs in
well under a second.
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

__all__ = [
    "SpreadTrader",
    "PairTrade",
    "PairResult",
    "pairs_weights",
    "half_life_ar1",
    "hedge_ratio",
    "HEDGE_METHODS",
]

HEDGE_METHODS: tuple[str, ...] = ("ols_log", "ratio")

_EPS = 1e-12


# --------------------------------------------------------------------------- #
# estimators                                                                  #
# --------------------------------------------------------------------------- #
def hedge_ratio(y: pd.Series | np.ndarray, x: pd.Series | np.ndarray, method: str = "ols_log") -> float:
    """Hedge ratio beta of leg A on leg B over a formation window.

    ``"ols_log"``: OLS slope of ``ln(y)`` on ``ln(x)`` with an intercept — the
    Engle-Granger cointegrating regression of §3 variant B.
    ``"ratio"``: mean price ratio ``mean(y/x)``, i.e. a units hedge (used for
    ETF/NAV and same-underlying spreads where beta is 1 by construction).

    Returns NaN when the window is degenerate (constant x, non-positive prices,
    fewer than 3 usable observations).
    """
    if method not in HEDGE_METHODS:
        raise ValueError(f"method must be one of {HEDGE_METHODS}, got {method!r}")
    ya = np.asarray(y, dtype=float)
    xa = np.asarray(x, dtype=float)
    ok = np.isfinite(ya) & np.isfinite(xa) & (ya > 0) & (xa > 0)
    if ok.sum() < 3:
        return float("nan")
    ya, xa = ya[ok], xa[ok]
    if method == "ratio":
        return float(np.mean(ya / xa))
    ly, lx = np.log(ya), np.log(xa)
    if np.std(lx) < _EPS:
        return float("nan")
    design = np.column_stack([np.ones_like(lx), lx])
    beta = np.linalg.lstsq(design, ly, rcond=None)[0]
    return float(beta[1])


def half_life_ar1(spread: pd.Series | np.ndarray) -> float:
    """Mean-reversion half-life in bars from an AR(1) / Ornstein-Uhlenbeck fit.

    Regress ``ds_t = a + b * s_{t-1}`` and return ``-ln(2)/ln(1+b)``.
    ``b >= 0`` (a random walk or an explosive spread) has no finite half-life →
    returns ``inf``, which the half-life filter rejects. §3: keep pairs with
    half-life roughly in [5, 40] trading days.
    """
    s = np.asarray(spread, dtype=float)
    s = s[np.isfinite(s)]
    if s.size < 10:
        return float("nan")
    lag = s[:-1]
    d = np.diff(s)
    design = np.column_stack([np.ones_like(lag), lag])
    coef = np.linalg.lstsq(design, d, rcond=None)[0]
    b = float(coef[1])
    if b >= -_EPS:
        return float("inf")
    phi = 1.0 + b
    if phi <= 0:                      # over-shooting AR(1): reverts within a bar
        return 0.0
    return float(-np.log(2.0) / np.log(phi))


# --------------------------------------------------------------------------- #
# results                                                                     #
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class PairTrade:
    """One completed (or still open) spread episode."""

    symbol_a: str
    symbol_b: str
    entry_ts: pd.Timestamp
    exit_ts: pd.Timestamp | None
    side: int                     # +1 = long spread (long A / short B), -1 = short spread
    beta: float
    z_entry: float
    z_exit: float | None
    bars_held: int
    exit_reason: str              # "target" | "stop" | "time" | "filter" | "open"


@dataclass
class PairResult:
    """Per-pair output of :meth:`SpreadTrader.run_pair`."""

    symbol_a: str
    symbol_b: str
    position: pd.Series           # -1 / 0 / +1, indexed by calendar
    beta: pd.Series               # hedge ratio in force at each bar
    z: pd.Series                  # spread z-score at each bar
    spread: pd.Series
    half_life: pd.Series          # estimate in force at each bar (NaN before first fit)
    tradable: pd.Series           # bool: passed the half-life filter at that bar
    trades: list[PairTrade] = field(default_factory=list)

    @property
    def entry_dates(self) -> pd.DatetimeIndex:
        return pd.DatetimeIndex([t.entry_ts for t in self.trades])

    @property
    def exit_dates(self) -> pd.DatetimeIndex:
        return pd.DatetimeIndex([t.exit_ts for t in self.trades if t.exit_ts is not None])


# --------------------------------------------------------------------------- #
# the engine                                                                  #
# --------------------------------------------------------------------------- #
class SpreadTrader:
    """Configurable pair-trading state machine, N pairs concurrently.

    Parameters (defaults follow ``01-arbitrage-relative-value/01`` §3 variant B)
    --------------------------------------------------------------------------
    formation_bars:
        window for the hedge-ratio and half-life fit (252 ≈ 12m; §3 range 6-18m
        for the distance method, 1-3y for cointegration).
    z_window:
        rolling window for the spread mean/std; §3 wants "3-5 half-lives",
        63 bars ≈ 3 half-lives at a 20-day half-life.
    z_in / z_out / z_stop:
        entry threshold (§3: 2.0, range 1.5-2.5), exit threshold (0.5, i.e.
        "close at spread crossing 0 or |z| < 0.5"), divergence stop (4.0, range
        3.5-4).
    max_holding_bars:
        hard time stop — §3's "or at trading-window end" (126 ≈ 6 months).
    method:
        hedge ratio estimator, see :func:`hedge_ratio`.
    min_half_life / max_half_life:
        the §3 tradability filter, in bars. A pair whose current estimate falls
        outside the band is not traded (and an open position is closed with
        reason ``"filter"``) until a later refit brings it back.
    refit_every:
        bars between hedge-ratio/half-life refits (21 ≈ monthly, matching §3's
        "overlapping cohorts — start a new formation/trading cycle monthly").
    gross:
        total gross exposure the whole pair book uses when every pair is on;
        each pair gets ``gross / n_pairs`` and splits it between its two legs as
        ``1 : |beta|`` so the legs are beta-weighted, not equal dollar (§3).
    """

    def __init__(
        self,
        formation_bars: int = 252,
        z_window: int = 63,
        z_in: float = 2.0,
        z_out: float = 0.5,
        z_stop: float = 4.0,
        max_holding_bars: int = 126,
        method: str = "ols_log",
        min_half_life: float = 5.0,
        max_half_life: float = 40.0,
        refit_every: int = 21,
        gross: float = 1.0,
        min_periods_frac: float = 0.75,
    ):
        if method not in HEDGE_METHODS:
            raise ValueError(f"method must be one of {HEDGE_METHODS}, got {method!r}")
        if not (0.0 <= z_out < z_in < z_stop):
            raise ValueError(f"need 0 <= z_out ({z_out}) < z_in ({z_in}) < z_stop ({z_stop})")
        self.formation_bars = int(formation_bars)
        self.z_window = int(z_window)
        self.z_in = float(z_in)
        self.z_out = float(z_out)
        self.z_stop = float(z_stop)
        self.max_holding_bars = int(max_holding_bars)
        self.method = method
        self.min_half_life = float(min_half_life)
        self.max_half_life = float(max_half_life)
        self.refit_every = max(1, int(refit_every))
        self.gross = float(gross)
        self.min_periods_frac = float(min_periods_frac)

    # ---------------- one pair ----------------
    def run_pair(self, px: pd.DataFrame, symbol_a: str, symbol_b: str) -> PairResult:
        """Run the state machine on one pair. O(n_bars) after the refits."""
        pa = px[symbol_a].astype(float)
        pb = px[symbol_b].astype(float)
        idx = px.index
        n = len(idx)

        a = pa.to_numpy(dtype=float)
        b = pb.to_numpy(dtype=float)
        pos = np.zeros(n, dtype=float)
        beta_arr = np.full(n, np.nan)
        z_arr = np.full(n, np.nan)
        sp_arr = np.full(n, np.nan)
        hl_arr = np.full(n, np.nan)
        ok_arr = np.zeros(n, dtype=bool)

        beta = float("nan")
        hl = float("nan")
        tradable = False
        state = 0                      # -1 short spread, 0 flat, +1 long spread
        entry_i = -1
        z_entry = float("nan")
        blocked = False                # set after any exit; cleared when |z| < z_out
        trades: list[PairTrade] = []
        min_z_obs = max(5, int(self.z_window * self.min_periods_frac))

        for i in range(n):
            # --- refit on the fixed calendar, using data strictly before i ---
            if i >= self.formation_bars and (i - self.formation_bars) % self.refit_every == 0:
                w0 = i - self.formation_bars
                beta = hedge_ratio(a[w0:i], b[w0:i], self.method)
                if np.isfinite(beta):
                    hl = half_life_ar1(_spread_arr(a[w0:i], b[w0:i], beta, self.method))
                    tradable = bool(
                        np.isfinite(hl) and self.min_half_life <= hl <= self.max_half_life
                    )
                else:
                    hl, tradable = float("nan"), False

            beta_arr[i] = beta
            hl_arr[i] = hl
            ok_arr[i] = tradable
            if not np.isfinite(beta):
                continue

            # --- spread level at i; mean/std over the window ending at i-1 ---
            s_i = _spread_scalar(a[i], b[i], beta, self.method)
            sp_arr[i] = s_i
            lo = max(0, i - self.z_window)
            hist = _spread_arr(a[lo:i], b[lo:i], beta, self.method)
            hist = hist[np.isfinite(hist)]
            if hist.size < min_z_obs or not np.isfinite(s_i):
                continue
            mu = float(hist.mean())
            sd = float(hist.std(ddof=0))
            if sd < _EPS:
                continue
            z = (s_i - mu) / sd
            z_arr[i] = z

            az = abs(z)
            if blocked and az < self.z_out:
                blocked = False

            # --- state machine ---
            if state != 0:
                reason = None
                if not tradable:
                    reason = "filter"
                elif az > self.z_stop:
                    reason = "stop"
                elif az < self.z_out:
                    reason = "target"
                elif (i - entry_i) >= self.max_holding_bars:
                    reason = "time"
                if reason is not None:
                    trades.append(
                        PairTrade(
                            symbol_a, symbol_b, idx[entry_i], idx[i], int(state), float(beta_arr[entry_i]),
                            float(z_entry), float(z), int(i - entry_i), reason,
                        )
                    )
                    state = 0
                    entry_i = -1
                    blocked = True
                    pos[i] = 0.0
                    continue
                pos[i] = float(state)
                continue

            if tradable and not blocked and self.z_in < az <= self.z_stop:
                state = -1 if z > 0 else 1      # spread rich → short it, cheap → long it
                entry_i = i
                z_entry = z
                pos[i] = float(state)

        if state != 0 and entry_i >= 0:
            trades.append(
                PairTrade(symbol_a, symbol_b, idx[entry_i], None, int(state),
                          float(beta_arr[entry_i]), float(z_entry), None, int(n - 1 - entry_i), "open")
            )

        return PairResult(
            symbol_a=symbol_a, symbol_b=symbol_b,
            position=pd.Series(pos, index=idx, name=f"{symbol_a}/{symbol_b}"),
            beta=pd.Series(beta_arr, index=idx),
            z=pd.Series(z_arr, index=idx),
            spread=pd.Series(sp_arr, index=idx),
            half_life=pd.Series(hl_arr, index=idx),
            tradable=pd.Series(ok_arr, index=idx),
            trades=trades,
        )

    # ---------------- N pairs ----------------
    def pairs_weights(
        self,
        px: pd.DataFrame,
        pairs: Sequence[tuple[str, str]],
        universe_mask: pd.DataFrame | None = None,
        return_details: bool = False,
    ) -> pd.DataFrame | tuple[pd.DataFrame, list[PairResult]]:
        """Weights frame for a book of pairs.

        Each pair gets a budget ``g = gross / n_pairs`` split between its legs as
        ``w_a = side * g / (1 + |beta|)`` and ``w_b = -side * beta * g / (1 + |beta|)``
        so ``|w_a| + |w_b| == g`` exactly and the legs are beta-weighted (§3).
        A symbol appearing in several pairs accumulates its legs.

        Parameters
        ----------
        px:
            price frame — ``ctx.close`` or ``ctx.total_return`` (TR is the
            correct input for equity pairs: dividends otherwise show up as fake
            spread divergence).
        pairs:
            ``[(A, B), ...]``; unknown symbols raise.
        universe_mask:
            optional; legs are zeroed on bars where either side is not tradable.
        return_details:
            also return the list of :class:`PairResult` (trade ledger, z-scores)
            for reporting / tests.
        """
        missing = sorted({s for p in pairs for s in p} - set(px.columns))
        if missing:
            raise KeyError(f"pairs reference symbols not in the price frame: {missing}")
        w = pd.DataFrame(0.0, index=px.index, columns=px.columns, dtype=float)
        results: list[PairResult] = []
        n_pairs = max(1, len(pairs))
        budget = self.gross / n_pairs

        for sym_a, sym_b in pairs:
            res = self.run_pair(px, sym_a, sym_b)
            results.append(res)
            beta = res.beta.abs().fillna(0.0)
            denom = (1.0 + beta).replace(0.0, np.nan)
            unit = budget / denom
            leg_a = res.position * unit
            leg_b = -res.position * res.beta.fillna(0.0) * unit
            w[sym_a] = w[sym_a].add(leg_a.fillna(0.0), fill_value=0.0)
            w[sym_b] = w[sym_b].add(leg_b.fillna(0.0), fill_value=0.0)

        if universe_mask is not None:
            m = universe_mask.reindex(index=w.index, columns=w.columns).fillna(False).astype(bool)
            w = w.where(m, 0.0)
        w = w.replace([np.inf, -np.inf], 0.0).fillna(0.0)
        return (w, results) if return_details else w


def _spread_scalar(a: float, b: float, beta: float, method: str) -> float:
    if method == "ratio":
        return float(a - beta * b)
    if not (a > 0 and b > 0):
        return float("nan")
    return float(np.log(a) - beta * np.log(b))


def _spread_arr(a: np.ndarray, b: np.ndarray, beta: float, method: str) -> np.ndarray:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if method == "ratio":
        return a - beta * b
    with np.errstate(invalid="ignore", divide="ignore"):
        out = np.where((a > 0) & (b > 0), np.log(np.where(a > 0, a, np.nan))
                       - beta * np.log(np.where(b > 0, b, np.nan)), np.nan)
    return out


def pairs_weights(
    px: pd.DataFrame,
    pairs: Sequence[tuple[str, str]],
    universe_mask: pd.DataFrame | None = None,
    return_details: bool = False,
    **params,
) -> pd.DataFrame | tuple[pd.DataFrame, list[PairResult]]:
    """Convenience wrapper: build a :class:`SpreadTrader` from ``**params`` and run it.

    ``pairs_weights(ctx.total_return, [("MOEX:LKOH", "MOEX:ROSN")], z_in=2.0)``
    """
    return SpreadTrader(**params).pairs_weights(
        px, pairs, universe_mask=universe_mask, return_details=return_details
    )
