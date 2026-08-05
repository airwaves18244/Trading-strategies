"""#25 Volatility carry (VIX-style roll). Doc: strategies/05-carry/04.
Requires vol_futures_curve (CSV; RVI futures are thin — user-supplied curve).
Basis-conditional short front vol with hard de-risk rules (§3)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from qbt.engine.context import DataContext
from qbt.strategy.base import Param, Signals, Strategy
from qbt.strategy.lib import vix_style_basis


class VolCarry(Strategy):
    key = "vol_carry"
    name = "Volatility Carry (basis-conditional)"
    doc_path = "strategies/05-carry/04-volatility-carry-vix-roll.md"
    output = "weights"
    group = "B"
    data_requirements = ("vol_futures_curve",)
    default_universe = "vol_futures"
    description = "Short front vol future when contango > θ; flat in the mush; exit pre-inversion (§3)."
    params = (
        Param("theta_short", 0.03, low=0.02, high=0.05, doc="contango entry threshold",
              source="05-carry/04 §3 (2-5%)"),
        Param("exit_level", 0.01, low=0.0, high=0.02, doc="de-risk when basis < this", source="§3"),
        Param("long_backwardation", False, choices=(True, False), source="§3 optional long leg"),
        Param("theta_long", -0.02, low=-0.05, high=-0.01),
        Param("size", 0.10, low=0.02, high=0.20, doc="weight of the vol position"),
    )

    def generate(self, ctx: DataContext) -> Signals:
        curve = vix_style_basis(ctx.events["vol_futures_curve"],
                                spot=ctx.extras.get("vol_spot", pd.DataFrame()).squeeze()
                                if "vol_spot" in ctx.extras else None)
        w = pd.DataFrame(0.0, index=ctx.calendar, columns=ctx.symbols)
        if not len(curve):
            return w
        sym = ctx.symbols[0]                       # tradable proxy instrument
        slope = curve["slope12"].reindex(ctx.calendar).ffill(limit=3)
        pos = pd.Series(0.0, index=ctx.calendar)
        state = 0.0
        for t in ctx.calendar:
            b = slope.get(t, np.nan)
            if not np.isfinite(b):
                pos[t] = state
                continue
            if state < 0 and b < self.p["exit_level"]:
                state = 0.0                        # de-risk before inversion
            if state == 0.0:
                if b > self.p["theta_short"]:
                    state = -self.p["size"]
                elif self.p["long_backwardation"] and b < self.p["theta_long"]:
                    state = self.p["size"]
            elif state > 0 and b > 0:
                state = 0.0                        # curve re-normalized: exit long
            pos[t] = state
        w[sym] = pos
        return w
