"""#41 Fundamental seasonality (Heston-Sadka cross-sectional variant). Doc: strategies/09-flows-seasonality/03.
Group A (needs only prices): rank stocks by their historical same-calendar-month
return over past years (§3-C). Dividend-month variant needs fundamentals — deferred."""
from __future__ import annotations

import numpy as np
import pandas as pd

from qbt.engine.context import DataContext
from qbt.strategy.base import Param, Signals, Strategy
from qbt.strategy.lib import cross_sectional_weights


class FundamentalSeasonality(Strategy):
    key = "fundamental_seasonality"
    name = "Cross-Sectional Return Seasonality"
    doc_path = "strategies/09-flows-seasonality/03-fundamental-seasonality.md"
    output = "weights"
    group = "A"
    default_universe = "moex_liquid"
    description = "Long stocks strong in this calendar month historically (§3-C, Heston-Sadka)."
    params = (
        Param("years_back", 5, low=3, high=10, step=1, doc="years of same-month history",
              source="09-…/03 §3-C (5-20y)"),
        Param("top_frac", 0.2, low=0.1, high=0.3),
        Param("long_only", True, choices=(True, False)),
    )

    def generate(self, ctx: DataContext) -> Signals:
        tr = ctx.total_return
        monthly = tr.resample("ME").last().pct_change(fill_method=None)
        # signal at month m = mean of returns in the same calendar month, past N years (strictly prior)
        same_month_mean = monthly.groupby(monthly.index.month).apply(
            lambda g: g.shift(1).rolling(self.p["years_back"], min_periods=2).mean()
        )
        same_month_mean = same_month_mean.reset_index(level=0, drop=True).sort_index()
        signal_m = same_month_mean
        # broadcast month-level signal to the daily calendar (known at month start: shift to prior month-end)
        signal = signal_m.reindex(ctx.calendar, method="ffill")
        return cross_sectional_weights(
            signal, ctx.universe_mask,
            top_frac=self.p["top_frac"], bottom_frac=self.p["top_frac"],
            long_only=self.p["long_only"], rebalance_dates=ctx.rebalance_dates("ME"),
        )
