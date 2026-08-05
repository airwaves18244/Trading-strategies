"""#8 Cross-sectional equity momentum (12-1). Doc: strategies/02-momentum/01."""
from __future__ import annotations

from qbt.engine.context import DataContext
from qbt.strategy.base import Param, Signals, Strategy
from qbt.strategy.lib import cross_sectional_weights, skip_month_return, trailing_vol


class XsEquityMomentum(Strategy):
    key = "xs_equity_momentum"
    name = "Cross-Sectional Equity Momentum (12-1)"
    doc_path = "strategies/02-momentum/01-cross-sectional-equity-momentum.md"
    output = "weights"
    group = "A"
    default_universe = "moex_liquid"
    description = ("Winners minus losers on 12-1 month total returns; skip-month, "
                   "monthly rebalance, optional sector neutrality (§3).")
    params = (
        Param("formation", 252, low=126, high=252, step=21, doc="formation window, bars",
              source="02-momentum/01 §3 (6-12m)"),
        Param("skip", 21, low=0, high=21, step=21, doc="skip window, bars (keep the skip)",
              source="02-momentum/01 §3"),
        Param("top_frac", 0.1, low=0.05, high=0.3, doc="long fractile", source="§3 deciles"),
        Param("bottom_frac", 0.1, low=0.05, high=0.3, doc="short fractile (0 if long-only)"),
        Param("long_only", True, choices=(True, False),
              doc="shorting MOEX equities is constrained post-2022", source="architecture §risks"),
        Param("sector_neutral", False, choices=(True, False), source="02-momentum/01 §3"),
        Param("weighting", "equal", choices=("equal", "inverse_vol"), source="§3"),
    )

    def generate(self, ctx: DataContext) -> Signals:
        signal = skip_month_return(ctx.total_return, formation=self.p["formation"],
                                   skip=self.p["skip"])
        sector_map = {s: (i.sector or "NA") for s, i in ctx.instruments.items()}
        vol = trailing_vol(ctx.ret()) if self.p["weighting"] == "inverse_vol" else None
        return cross_sectional_weights(
            signal, ctx.universe_mask,
            top_frac=self.p["top_frac"], bottom_frac=self.p["bottom_frac"],
            long_only=self.p["long_only"],
            sector_map=sector_map, sector_neutral=self.p["sector_neutral"],
            weighting=self.p["weighting"], vol=vol,
            rebalance_dates=ctx.rebalance_dates("ME"),
        )
