"""#21 Overnight/intraday decomposition. Doc: strategies/04-mean-reversion-swing/04.
Variant B (conditional overnight drift): hold close->open only after down intraday
sessions in high-vol states. Daily OHLC suffices (overnight = close->next open)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from qbt.engine.context import DataContext
from qbt.strategy.base import Param, Signals, Strategy


class OvernightIntraday(Strategy):
    key = "overnight_intraday"
    name = "Conditional Overnight Drift"
    doc_path = "strategies/04-mean-reversion-swing/04-overnight-intraday-decomposition.md"
    output = "weights"
    group = "A"
    default_universe = "moex_index"
    description = ("Overnight index exposure conditional on down intraday + vol state (§3-B). "
                   "NOTE: weights engine approximates the overnight leg with daily bars; "
                   "treat results as upper-bound research (§7 open-price caveat).")
    params = (
        Param("intraday_dn_thresh", 0.0, low=-0.02, high=0.0, doc="enter if open->close < this",
              source="04-…/04 §3-B"),
        Param("vol_mult", 1.2, low=1.0, high=2.0, doc="5d vol must exceed mult× 60d vol"),
        Param("exposure", 1.0, low=0.2, high=1.5),
    )

    def generate(self, ctx: DataContext) -> Signals:
        sym = ctx.symbols[0]
        intraday = ctx.close[sym] / ctx.open[sym] - 1.0
        r = ctx.close[sym].pct_change(fill_method=None)
        v5 = r.rolling(5).std()
        v60 = r.rolling(60).std()
        cond = (intraday < self.p["intraday_dn_thresh"]) & (v5 > self.p["vol_mult"] * v60)
        w = pd.DataFrame(0.0, index=ctx.calendar, columns=ctx.symbols)
        w[sym] = np.where(cond, self.p["exposure"], 0.0)
        return w
