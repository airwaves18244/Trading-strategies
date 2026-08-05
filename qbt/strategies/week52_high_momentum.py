"""#12 52-week-high momentum (anchoring). Doc: strategies/02-momentum/05."""
from __future__ import annotations

from qbt.engine.context import DataContext
from qbt.strategy.base import Param, Signals, Strategy
from qbt.strategy.lib import cross_sectional_weights


class Week52HighMomentum(Strategy):
    key = "week52_high_momentum"
    name = "52-Week-High Momentum"
    doc_path = "strategies/02-momentum/05-52-week-high-momentum.md"
    output = "weights"
    group = "A"
    default_universe = "moex_liquid"
    description = "Rank by proximity of price to its 252-day high (anchoring, §3)."
    params = (
        Param("high_window", 252, low=126, high=378, step=21,
              doc="lookback for the reference high", source="02-momentum/05 §3"),
        Param("top_frac", 0.1, low=0.05, high=0.3),
        Param("long_only", True, choices=(True, False)),
        Param("sector_neutral", False, choices=(True, False), source="§3 refinement"),
    )

    def generate(self, ctx: DataContext) -> Signals:
        # adjusted-price discipline (§7): use the TR series for both price and high
        px = ctx.total_return
        high = px.rolling(self.p["high_window"], min_periods=self.p["high_window"] // 2).max()
        signal = px / high
        sector_map = {s: (i.sector or "NA") for s, i in ctx.instruments.items()}
        return cross_sectional_weights(
            signal, ctx.universe_mask,
            top_frac=self.p["top_frac"], bottom_frac=self.p["top_frac"],
            long_only=self.p["long_only"],
            sector_map=sector_map, sector_neutral=self.p["sector_neutral"],
            rebalance_dates=ctx.rebalance_dates("ME"),
        )
