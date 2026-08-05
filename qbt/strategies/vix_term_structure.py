"""#28 VIX-style term-structure state machine (two-sided). Doc: strategies/06-volatility/02.
Requires vol_futures_curve. States: calm-carry short / transition flat / panic long."""
from __future__ import annotations

import numpy as np
import pandas as pd

from qbt.engine.context import DataContext
from qbt.strategy.base import Param, Signals, Strategy
from qbt.strategy.lib import vix_style_basis


class VixTermStructure(Strategy):
    key = "vix_term_structure"
    name = "Vol Term-Structure State Machine"
    doc_path = "strategies/06-volatility/02-vix-term-structure-trading.md"
    output = "weights"
    group = "B"
    data_requirements = ("vol_futures_curve",)
    default_universe = "vol_futures"
    description = "Short vol in steep contango, long early backwardation, hysteresis (§3)."
    params = (
        Param("contango_in", 0.03, low=0.02, high=0.05, source="06-…/02 §3"),
        Param("contango_out", 0.01, low=0.0, high=0.02, doc="hysteresis exit"),
        Param("inversion_in", -0.02, low=-0.05, high=-0.01, source="§3 panic state"),
        Param("inversion_max_age", 10, low=5, high=15, doc="skip late-inversion longs", source="§3"),
        Param("size_short", 0.08, low=0.02, high=0.15),
        Param("size_long", 0.12, low=0.04, high=0.25, doc="long leg sized larger (positive skew side)"),
    )

    def generate(self, ctx: DataContext) -> Signals:
        curve = vix_style_basis(ctx.events["vol_futures_curve"])
        w = pd.DataFrame(0.0, index=ctx.calendar, columns=ctx.symbols)
        if not len(curve):
            return w
        sym = ctx.symbols[0]
        slope = curve["slope12"].reindex(ctx.calendar).ffill(limit=3)
        pos = pd.Series(0.0, index=ctx.calendar)
        state, inv_age = 0.0, 0
        for t in ctx.calendar:
            b = slope.get(t, np.nan)
            if not np.isfinite(b):
                pos[t] = state
                continue
            inv_age = inv_age + 1 if b < 0 else 0
            if state < 0:                                    # in short-vol state
                if b < self.p["contango_out"]:
                    state = 0.0
            elif state > 0:                                  # in long-vol state
                if b > 0:
                    state = 0.0
            if state == 0.0:
                if b > self.p["contango_in"]:
                    state = -self.p["size_short"]
                elif b < self.p["inversion_in"] and inv_age <= self.p["inversion_max_age"]:
                    state = self.p["size_long"]
            pos[t] = state
        w[sym] = pos
        return w
