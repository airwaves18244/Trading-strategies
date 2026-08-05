"""#23 Commodity carry (backwardation/roll yield). Doc: strategies/05-carry/02.
Needs ctx.extras['basis_ann'] (built by DataService/WS-F from FORTS chains).
Degrades to empty weights when absent."""
from __future__ import annotations

import pandas as pd

from qbt.engine.context import DataContext
from qbt.strategy.base import Param, Signals, Strategy
from qbt.strategy.lib import carry_xs_signal, deseasonalized_slope, has_extras, to_weights, trailing_vol


class CommodityCarry(Strategy):
    key = "commodity_carry"
    name = "Commodity Carry (curve slope)"
    doc_path = "strategies/05-carry/02-commodity-carry.md"
    output = "weights"
    group = "A"
    default_universe = "forts_core"
    description = "Long backwardated / short contangoed markets, deseasonalized slope (§3)."
    params = (
        Param("deseasonalize", True, choices=(True, False), source="05-carry/02 §3 (mandatory for ags/gas)"),
        Param("per_asset_target", 0.10, low=0.05, high=0.25),
        Param("clamp", 2.0, low=1.0, high=3.0, doc="carry z-score clamp"),
    )

    def generate(self, ctx: DataContext) -> Signals:
        if not has_extras(ctx, "basis_ann"):
            return pd.DataFrame(0.0, index=ctx.calendar, columns=ctx.symbols)
        basis = ctx.extras["basis_ann"].reindex(index=ctx.calendar).ffill(limit=5)
        if self.p["deseasonalize"]:
            basis = deseasonalized_slope(basis)
        signal = carry_xs_signal(basis, clamp=self.p["clamp"]) / self.p["clamp"]
        signal = signal.reindex(columns=ctx.symbols).fillna(0.0)
        vol = trailing_vol(ctx.ret())
        return to_weights(signal, vol=vol, per_asset_target=self.p["per_asset_target"],
                          ann_factor=ctx.ann_factor, universe_mask=ctx.universe_mask)
