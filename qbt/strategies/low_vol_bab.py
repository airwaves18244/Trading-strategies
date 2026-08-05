"""#38 Low-volatility / betting-against-beta. Doc: strategies/08-value-fundamental-factor/03.

Default = long-only defensive (variant B of §3): overweight lowest-vol quintile
within sectors. BAB long-short available via long_only=False (research-only on
MOEX given borrow constraints).
"""
from __future__ import annotations

from qbt.engine.context import DataContext
from qbt.strategy.base import Param, Signals, Strategy
from qbt.strategy.lib import cross_sectional_weights, trailing_vol


class LowVolBab(Strategy):
    key = "low_vol_bab"
    name = "Low-Volatility / Defensive"
    doc_path = "strategies/08-value-fundamental-factor/03-low-volatility-betting-against-beta.md"
    output = "weights"
    group = "A"
    default_universe = "moex_liquid"
    description = "Long low-vol quintile, sector-neutral (§3-B); optional short high-vol."
    params = (
        Param("vol_window", 252, low=126, high=504, step=21,
              doc="realized vol estimation window", source="08-…/03 §3 (1y)"),
        Param("top_frac", 0.2, low=0.1, high=0.4),
        Param("long_only", True, choices=(True, False)),
        Param("sector_neutral", True, choices=(True, False), source="§3-B"),
    )

    def generate(self, ctx: DataContext) -> Signals:
        vol = trailing_vol(ctx.ret(), window=self.p["vol_window"])
        signal = -vol  # low vol = high rank
        sector_map = {s: (i.sector or "NA") for s, i in ctx.instruments.items()}
        return cross_sectional_weights(
            signal, ctx.universe_mask,
            top_frac=self.p["top_frac"], bottom_frac=self.p["top_frac"],
            long_only=self.p["long_only"],
            sector_map=sector_map, sector_neutral=self.p["sector_neutral"],
            rebalance_dates=ctx.rebalance_dates("ME"), min_names=2,
        )
