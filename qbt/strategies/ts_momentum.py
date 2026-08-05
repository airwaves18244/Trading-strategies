"""#9 Time-series momentum (multi-asset). Doc: strategies/02-momentum/02."""
from __future__ import annotations

from qbt.engine.context import DataContext
from qbt.strategy.base import Param, Signals, Strategy
from qbt.strategy.lib import to_weights, trailing_vol, ts_ensemble


class TsMomentum(Strategy):
    key = "ts_momentum"
    name = "Time-Series Momentum (TSMOM)"
    doc_path = "strategies/02-momentum/02-time-series-momentum.md"
    output = "weights"
    group = "A"
    default_universe = "forts_core"
    description = "Sign of 1/3/12m returns per market, inverse-vol sized, class risk caps (§3)."
    params = (
        Param("lookbacks", "21,63,252", doc="comma-separated lookbacks, bars",
              source="02-momentum/02 §3 (1/3/12m ensemble)"),
        Param("per_asset_target", 0.15, low=0.05, high=0.40,
              doc="annualized vol per market at full signal", source="§3"),
        Param("vol_window", 63, low=20, high=120, doc="ex-ante vol estimation window"),
        Param("max_gross", 4.0, low=1.0, high=8.0, doc="futures book gross cap"),
    )

    def generate(self, ctx: DataContext) -> Signals:
        lookbacks = tuple(int(x) for x in str(self.p["lookbacks"]).split(","))
        signal = ts_ensemble(ctx.total_return, lookbacks=lookbacks, kind="return_sign")
        vol = trailing_vol(ctx.ret(), window=self.p["vol_window"])
        group_map = {s: str(i.asset_class) for s, i in ctx.instruments.items()}
        return to_weights(
            signal, vol=vol, per_asset_target=self.p["per_asset_target"],
            group_map=group_map, group_risk_caps={g: 0.4 for g in set(group_map.values())},
            ann_factor=ctx.ann_factor, max_gross=self.p["max_gross"],
            universe_mask=ctx.universe_mask,
        )
