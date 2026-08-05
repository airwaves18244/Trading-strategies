"""#39 Turn-of-month flows. Doc: strategies/09-flows-seasonality/01."""
from __future__ import annotations

import numpy as np
import pandas as pd

from qbt.engine.context import DataContext
from qbt.strategy.base import Param, Signals, Strategy


class TurnOfMonth(Strategy):
    key = "turn_of_month"
    name = "Turn-of-Month Harvest"
    doc_path = "strategies/09-flows-seasonality/01-turn-of-month-rebalancing-flows.md"
    output = "weights"
    group = "A"
    default_universe = "moex_index"
    description = "Long index only from T-1 (last day) through T+3 of each month (§3-A)."
    params = (
        Param("days_before", 1, low=0, high=4, doc="enter N trading days before month-end",
              source="09-…/01 §3-A (T-4..T-1)"),
        Param("days_after", 3, low=2, high=5, doc="exit after N days of the new month", source="§3-A"),
        Param("exposure", 1.0, low=0.2, high=1.5),
    )

    def generate(self, ctx: DataContext) -> Signals:
        cal = ctx.calendar
        month_ends = ctx.rebalance_dates("ME")
        in_window = pd.Series(False, index=cal)
        pos_of = {ts: i for i, ts in enumerate(cal)}
        for me in month_ends:
            i = pos_of.get(me)
            if i is None:
                continue
            lo = max(0, i - self.p["days_before"] + 1)
            hi = min(len(cal), i + self.p["days_after"] + 1)
            in_window.iloc[lo:hi] = True
        w = pd.DataFrame(0.0, index=cal, columns=ctx.symbols)
        w[ctx.symbols[0]] = np.where(in_window, self.p["exposure"], 0.0)
        return w
