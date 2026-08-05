"""#6 Futures calendar-spread / term-structure RV. Doc: strategies/01-arbitrage-relative-value/06.
Signal 2 of §3 (spread momentum as inventory proxy) on ctx.extras['spread_series']
(long-format frame: columns per market = near-far spread level, roll-adjusted)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from qbt.engine.context import DataContext
from qbt.strategy.base import Param, Signals, Strategy
from qbt.strategy.lib import has_extras


class CalendarSpreadRv(Strategy):
    key = "calendar_spread_rv"
    name = "Calendar-Spread Term-Structure RV"
    doc_path = "strategies/01-arbitrage-relative-value/06-futures-calendar-spread-term-structure-rv.md"
    output = "weights"
    group = "A"
    default_universe = "forts_core"
    description = ("Spread-momentum (tightening → long near/short far) via continuous spread "
                   "series; positions expressed on the near-leg proxy (§3 signal-2).")
    params = (
        Param("mom_window", 42, low=21, high=84, step=7, doc="spread momentum lookback",
              source="01-…/06 §3 (1-3m)"),
        Param("per_spread", 0.05, low=0.01, high=0.10, doc="risk per market", source="§3 (≤0.5% NAV risk)"),
        Param("hold_weeks", 6, low=2, high=8, source="§3 (2-8 weeks)"),
    )

    def generate(self, ctx: DataContext) -> Signals:
        w = pd.DataFrame(0.0, index=ctx.calendar, columns=ctx.symbols)
        if not has_extras(ctx, "spread_series"):
            return w
        sp = ctx.extras["spread_series"].reindex(index=ctx.calendar).ffill(limit=5)
        mom = sp.diff(self.p["mom_window"])
        rebal = ctx.rebalance_dates("W")
        sig = np.sign(mom).reindex(rebal).reindex(ctx.calendar).ffill(limit=self.p["hold_weeks"] * 5)
        for m in sp.columns:
            if m in w.columns:
                w[m] = sig[m].fillna(0.0) * self.p["per_spread"]
        return w
