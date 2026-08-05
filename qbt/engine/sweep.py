"""Parameter sweeps -> tidy DataFrame for the heatmap (WS-C)."""
from __future__ import annotations

import itertools
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import pandas as pd

from qbt.engine.context import DataContext
from qbt.engine.costs import CostModel
from qbt.strategy.base import Strategy


def sweep(
    strategy_cls: type[Strategy],
    base_params: dict[str, Any],
    grid: dict[str, list[Any]],
    ctx: DataContext,
    cost_model: CostModel | None = None,
    metric_keys: tuple[str, ...] = ("sharpe", "max_dd", "cagr", "turnover_ann"),
    n_jobs: int = 2,
    progress_cb=None,
    **run_kwargs: Any,
) -> pd.DataFrame:
    """Cartesian product over `grid` (1-2 params recommended); one tidy row per combo."""
    from qbt.engine.runner import run_backtest

    names = list(grid)
    combos = list(itertools.product(*(grid[k] for k in names)))

    def one(combo: tuple) -> dict[str, Any]:
        params = dict(base_params)
        params.update(dict(zip(names, combo)))
        row: dict[str, Any] = dict(zip(names, combo))
        try:
            res = run_backtest(strategy_cls(**params), ctx, cost_model=cost_model, **run_kwargs)
            for k in metric_keys:
                row[k] = res.metrics.get(k)
            row["error"] = None
        except Exception as e:  # noqa: BLE001 - a failing cell must not kill the sweep
            for k in metric_keys:
                row[k] = None
            row["error"] = f"{type(e).__name__}: {e}"
        return row

    rows: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max(1, n_jobs)) as ex:
        for i, row in enumerate(ex.map(one, combos)):
            rows.append(row)
            if progress_cb:
                progress_cb((i + 1) / len(combos))
    return pd.DataFrame(rows)
