"""#15 Managed-futures trend (EWMA crossover ensemble). Doc: strategies/03-trend-following/01."""
from __future__ import annotations

from qbt.engine.context import DataContext
from qbt.strategy.base import Param, Signals, Strategy
from qbt.strategy.lib import to_weights, trailing_vol, ts_ensemble


class ManagedFuturesTrend(Strategy):
    key = "managed_futures_trend"
    name = "Managed-Futures Trend (EWMA ensemble)"
    doc_path = "strategies/03-trend-following/01-managed-futures-trend.md"
    output = "weights"
    group = "A"
    default_universe = "forts_core"
    description = "EWMA crossover pairs (8,24)/(16,48)/(32,96), squashed, vol-targeted (§3)."
    params = (
        Param("per_asset_target", 0.15, low=0.05, high=0.40, source="03-…/01 §3"),
        Param("vol_window", 63, low=20, high=120),
        Param("max_gross", 4.0, low=1.0, high=8.0),
    )

    def generate(self, ctx: DataContext) -> Signals:
        signal = ts_ensemble(ctx.total_return, kind="ewma_xover")
        vol = trailing_vol(ctx.ret(), window=self.p["vol_window"])
        group_map = {s: str(i.asset_class) for s, i in ctx.instruments.items()}
        return to_weights(
            signal, vol=vol, per_asset_target=self.p["per_asset_target"],
            group_map=group_map, group_risk_caps={g: 0.4 for g in set(group_map.values())},
            ann_factor=ctx.ann_factor, max_gross=self.p["max_gross"],
            universe_mask=ctx.universe_mask,
        )
