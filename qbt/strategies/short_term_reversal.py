"""#18 Short-term cross-sectional reversal. Doc: strategies/04-mean-reversion-swing/01.

Industry-relative residual reversal (§3 refinement): rank on r_stock − r_sector
over the past week; weekly rebalance. The cost model decides the sign — always
run the 2x-cost stress on this one (§7).
"""
from __future__ import annotations

from qbt.engine.context import DataContext
from qbt.strategy.base import Param, Signals, Strategy
from qbt.strategy.lib import cross_sectional_weights


class ShortTermReversal(Strategy):
    key = "short_term_reversal"
    name = "Short-Term Cross-Sectional Reversal"
    doc_path = "strategies/04-mean-reversion-swing/01-short-term-cross-sectional-reversal.md"
    output = "weights"
    group = "A"
    default_universe = "moex_liquid"
    description = "Buy last week's industry-relative losers, sell winners; weekly (§3)."
    params = (
        Param("formation", 5, low=3, high=10, step=1, doc="reversal window, bars",
              source="04-mean-reversion-swing/01 §3 (3-10d)"),
        Param("top_frac", 0.2, low=0.1, high=0.3),
        Param("industry_relative", True, choices=(True, False), source="§3 refinement"),
        Param("long_only", False, choices=(True, False),
              doc="reversal is inherently two-sided; long-only variant is weak"),
    )

    def generate(self, ctx: DataContext) -> Signals:
        f = self.p["formation"]
        ret_f = ctx.total_return.pct_change(f, fill_method=None)
        if self.p["industry_relative"]:
            sector_map = {s: (i.sector or "NA") for s, i in ctx.instruments.items()}
            sec = ret_f.T.groupby(lambda s: sector_map.get(s, "NA")).transform("mean").T
            signal = -(ret_f - sec)
        else:
            signal = -ret_f
        return cross_sectional_weights(
            signal, ctx.universe_mask,
            top_frac=self.p["top_frac"], bottom_frac=self.p["top_frac"],
            long_only=self.p["long_only"],
            rebalance_dates=ctx.rebalance_dates("W"),
        )
