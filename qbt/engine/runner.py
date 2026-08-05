"""run_backtest — the single entry point dispatching on Strategy.output (WS-C)."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from qbt.core.errors import DataGapError
from qbt.engine.context import DataContext
from qbt.engine.cost_models import load_cost_preset
from qbt.engine.costs import CostModel
from qbt.engine.orders import OrderEngine
from qbt.engine.result import BacktestResult, RunMeta
from qbt.engine.risk import apply_caps, vol_target
from qbt.engine.weights import WeightEngine
from qbt.strategy.base import Overlay, Strategy

log = logging.getLogger("qbt.runner")


def run_backtest(
    strategy: Strategy,
    ctx: DataContext,
    cost_model: CostModel | None = None,
    lag: int = 1,
    overlay: Overlay | None = None,
    vol_target_cfg: dict[str, Any] | None = None,
    caps_cfg: dict[str, Any] | None = None,
    initial_nav: float = 1.0,
    cost_preset_name: str = "moex_equity",
    run_id: str | None = None,
) -> BacktestResult:
    missing = strategy.check_data(ctx)
    if missing:
        raise DataGapError(
            f"Strategy '{strategy.key}' requires event tables missing from the context: {missing}. "
            f"Provide them via CSV import (see qbt/data/schemas.py) or run with synthetic fixtures."
        )
    cost_model = cost_model or load_cost_preset(cost_preset_name)

    meta = RunMeta(
        run_id=run_id or uuid.uuid4().hex[:12],
        strategy_key=strategy.key,
        params=dict(strategy.p),
        universe=strategy.default_universe,
        start=str(ctx.calendar[0].date()) if len(ctx.calendar) else "",
        end=str(ctx.calendar[-1].date()) if len(ctx.calendar) else "",
        freq=str(ctx.freq),
        cost_preset=cost_preset_name,
        execution_lag=lag,
        overlay=getattr(overlay, "name", None),
        created_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        engine=strategy.output,
    )

    signals = strategy.generate(ctx)

    if strategy.output == "orders":
        if overlay is not None:
            log.warning("Overlay '%s' ignored: '%s' is an order strategy (sizing embedded in intents).",
                        getattr(overlay, "name", overlay), strategy.key)
        if not isinstance(signals, list):
            raise TypeError(f"{strategy.key} declares output='orders' but returned {type(signals)}")
        return OrderEngine().run(signals, ctx, cost_model, initial_nav=initial_nav, meta=meta)

    if not isinstance(signals, pd.DataFrame):
        raise TypeError(f"{strategy.key} declares output='weights' but returned {type(signals)}")
    weights = signals

    if overlay is not None:
        if getattr(strategy, "compatible_overlays", None) == ():
            log.warning("Strategy '%s' declares itself overlay-incompatible (counter-cyclical); "
                        "applying '%s' anyway per explicit request — verify this is intended.",
                        strategy.key, getattr(overlay, "name", overlay))
        weights = overlay.transform(weights, ctx)

    if vol_target_cfg:
        weights = vol_target(weights, ctx.ret(), **vol_target_cfg)
    if caps_cfg:
        weights = apply_caps(weights, **caps_cfg)

    return WeightEngine().run(weights, ctx, cost_model, lag=lag, initial_nav=initial_nav, meta=meta)
