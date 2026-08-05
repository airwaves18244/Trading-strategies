"""Anti-fake-alpha harness (WS-C): look-ahead detection and cost-sensitivity."""
from __future__ import annotations

import numpy as np
import pandas as pd

from qbt.core.errors import LookaheadError
from qbt.engine.context import DataContext
from qbt.strategy.base import Strategy


def _default_cut_dates(ctx: DataContext, k: int = 3) -> list[pd.Timestamp]:
    cal = ctx.calendar
    if len(cal) < 20:
        return [cal[len(cal) // 2]] if len(cal) else []
    picks = [int(len(cal) * f) for f in (0.5, 0.75, 0.9)][:k]
    return [cal[i] for i in picks]


def assert_no_lookahead(
    strategy: Strategy,
    ctx: DataContext,
    cut_dates: list[pd.Timestamp] | None = None,
    atol: float = 1e-10,
) -> None:
    """generate(full) restricted to <=t must equal generate(ctx.slice(t)).

    Raises LookaheadError naming the first offending date/symbol.
    """
    cuts = cut_dates or _default_cut_dates(ctx)
    full = strategy.generate(ctx)
    for t in cuts:
        part = strategy.generate(ctx.slice(t))
        if isinstance(full, pd.DataFrame):
            a = full.loc[full.index <= t].fillna(0.0)
            b = part.loc[part.index <= t].reindex_like(a).fillna(0.0)
            diff = (a - b).abs()
            if float(diff.to_numpy().max(initial=0.0)) > atol:
                stacked = diff.stack()
                bad = stacked[stacked > atol]
                ts, sym = bad.index[0]
                raise LookaheadError(
                    f"{strategy.key}: signal at {ts:%Y-%m-%d}/{sym} changes when future data "
                    f"is removed (cut={t:%Y-%m-%d}, |Δ|={bad.iloc[0]:.3g})"
                )
        else:
            key = lambda o: (pd.Timestamp(o.ts), o.symbol, o.side, o.size_mode, round(o.size, 12))
            a = sorted(key(o) for o in full if pd.Timestamp(o.ts) <= t)
            b = sorted(key(o) for o in part if pd.Timestamp(o.ts) <= t)
            if a != b:
                raise LookaheadError(
                    f"{strategy.key}: order intents before {t:%Y-%m-%d} differ when future "
                    f"data is removed ({len(a)} vs {len(b)} intents)"
                )


def cost_sensitivity(
    strategy: Strategy,
    ctx: DataContext,
    cost_model,
    mult: float = 2.0,
    strict: bool = False,
) -> dict[str, dict[str, float]]:
    """Run at 1x and mult× costs; net Sharpe must not improve with higher costs."""
    from qbt.engine.cost_models import scale_cost_model
    from qbt.engine.runner import run_backtest

    base = run_backtest(strategy, ctx, cost_model=cost_model)
    stressed = run_backtest(strategy, ctx, cost_model=scale_cost_model(cost_model, mult))
    s0, s1 = base.metrics.get("sharpe", np.nan), stressed.metrics.get("sharpe", np.nan)
    if strict and np.isfinite(s0) and np.isfinite(s1) and s1 > s0 + 1e-9:
        raise AssertionError(f"{strategy.key}: net Sharpe improved under {mult}x costs ({s0:.3f} -> {s1:.3f})")
    return {"base": base.metrics, "stressed": stressed.metrics}
