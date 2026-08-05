"""#37 Cross-asset value (5y reversal anchor). Doc: strategies/08-value-fundamental-factor/02.
Asness convention for assets without fundamentals: value = −(past 5y return)."""
from __future__ import annotations

from qbt.engine.context import DataContext
from qbt.strategy.base import Param, Signals, Strategy
from qbt.strategy.lib import cross_sectional_weights, trailing_vol


class CrossAssetValue(Strategy):
    key = "cross_asset_value"
    name = "Cross-Asset Value (long-run reversal)"
    doc_path = "strategies/08-value-fundamental-factor/02-cross-asset-value.md"
    output = "weights"
    group = "A"
    default_universe = "forts_core"
    description = "Long assets depressed vs 5y ago, short extended; monthly, tiny turnover (§3)."
    params = (
        Param("reversal_years", 5, low=3, high=7, step=1, source="08-…/02 §3 (5y anchor)"),
        Param("top_frac", 0.33, low=0.2, high=0.5),
    )

    def generate(self, ctx: DataContext) -> Signals:
        lb = int(self.p["reversal_years"] * 252)
        signal = -ctx.total_return.pct_change(lb, fill_method=None)
        vol = trailing_vol(ctx.ret())
        return cross_sectional_weights(
            signal, ctx.universe_mask,
            top_frac=self.p["top_frac"], bottom_frac=self.p["top_frac"],
            long_only=False, weighting="inverse_vol", vol=vol,
            rebalance_dates=ctx.rebalance_dates("ME"), min_names=3,
        )
