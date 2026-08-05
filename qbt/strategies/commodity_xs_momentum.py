"""#14 Commodity cross-sectional momentum. Doc: strategies/02-momentum/07."""
from __future__ import annotations

from qbt.engine.context import DataContext
from qbt.strategy.base import Param, Signals, Strategy
from qbt.strategy.lib import cross_sectional_weights, trailing_vol


class CommodityXsMomentum(Strategy):
    key = "commodity_xs_momentum"
    name = "Commodity Cross-Sectional Momentum"
    doc_path = "strategies/02-momentum/07-commodity-cross-sectional-momentum.md"
    output = "weights"
    group = "A"
    default_universe = "forts_commodities"
    description = "Long top-third / short bottom-third by 12m return, inverse-vol, sector caps (§3)."
    params = (
        Param("formation", 252, low=63, high=252, step=21, source="02-momentum/07 §3 (3-12m)"),
        Param("top_frac", 0.33, low=0.2, high=0.5, source="§3 quartile/third"),
        Param("long_only", False, choices=(True, False), doc="futures: shorts fine"),
    )

    def generate(self, ctx: DataContext) -> Signals:
        signal = ctx.total_return.pct_change(self.p["formation"], fill_method=None)
        vol = trailing_vol(ctx.ret())
        sector_map = {s: (i.sector or "NA") for s, i in ctx.instruments.items()}
        return cross_sectional_weights(
            signal, ctx.universe_mask,
            top_frac=self.p["top_frac"], bottom_frac=self.p["top_frac"],
            long_only=self.p["long_only"], weighting="inverse_vol", vol=vol,
            sector_map=sector_map, sector_neutral=False,
            rebalance_dates=ctx.rebalance_dates("ME"), min_names=3,
        )
