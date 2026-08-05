"""#17 Trend + carry combined (signal-level blend). Doc: strategies/03-trend-following/03."""
from __future__ import annotations

import pandas as pd

from qbt.engine.context import DataContext
from qbt.strategy.base import Param, Signals, Strategy
from qbt.strategy.lib import carry_ts_signal, has_extras, to_weights, trailing_vol, ts_ensemble


class TrendPlusCarry(Strategy):
    key = "trend_plus_carry"
    name = "Trend + Carry Blend"
    doc_path = "strategies/03-trend-following/03-trend-plus-carry.md"
    output = "weights"
    group = "A"
    default_universe = "forts_core"
    description = "s = w_T·trend + w_C·carry per market; netted book, one weight set (§3)."
    params = (
        Param("w_trend", 0.6, low=0.5, high=0.7, doc="trend weight in the blend",
              source="03-…/03 §3 (0.5-0.7)"),
        Param("per_asset_target", 0.15, low=0.05, high=0.30),
    )

    def generate(self, ctx: DataContext) -> Signals:
        trend = ts_ensemble(ctx.total_return, kind="return_sign")
        if has_extras(ctx, "basis_ann"):
            basis = ctx.extras["basis_ann"].reindex(index=ctx.calendar).ffill(limit=5)
            carry = carry_ts_signal(basis).reindex(columns=ctx.symbols).fillna(0.0)
        else:
            carry = pd.DataFrame(0.0, index=ctx.calendar, columns=ctx.symbols)
        wt = self.p["w_trend"]
        signal = (wt * trend.reindex(columns=ctx.symbols).fillna(0.0)
                  + (1 - wt) * carry).clip(-1, 1)
        vol = trailing_vol(ctx.ret())
        group_map = {s: str(i.asset_class) for s, i in ctx.instruments.items()}
        return to_weights(signal, vol=vol, per_asset_target=self.p["per_asset_target"],
                          group_map=group_map,
                          group_risk_caps={g: 0.4 for g in set(group_map.values())},
                          ann_factor=ctx.ann_factor, universe_mask=ctx.universe_mask)
