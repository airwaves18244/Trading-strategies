"""#40 Commodity index roll congestion. Doc: strategies/09-flows-seasonality/02.
Requires roll_calendar. Trades the pre-roll window on the spread proxy — mostly
a decay-curve research vehicle (§2: naive trade documented dead)."""
from __future__ import annotations

import pandas as pd

from qbt.engine.context import DataContext
from qbt.strategy.base import Param, Signals, Strategy


class RollCongestion(Strategy):
    key = "roll_congestion"
    name = "Index Roll Congestion (research)"
    doc_path = "strategies/09-flows-seasonality/02-commodity-index-roll-congestion.md"
    output = "weights"
    group = "B"
    data_requirements = ("roll_calendar",)
    default_universe = "forts_commodities"
    description = "Pre-position before published index roll windows; unwind after (§3)."
    params = (
        Param("pre_days", 5, low=3, high=8, doc="enter N bars before roll_start", source="09-…/02 §3"),
        Param("per_market", 0.03, low=0.01, high=0.05),
    )

    def generate(self, ctx: DataContext) -> Signals:
        rolls = ctx.events["roll_calendar"]
        w = pd.DataFrame(0.0, index=ctx.calendar, columns=ctx.symbols)
        # asset_code -> tradable symbol containing that code (continuous root convention)
        code_map = {}
        for s in ctx.symbols:
            for code in rolls["asset_code"].astype(str).unique():
                if code and code in s:
                    code_map.setdefault(code, s)
        for i in rolls.index:
            code = str(rolls.at[i, "asset_code"])
            sym = code_map.get(code)
            if sym is None:
                continue
            start = pd.to_datetime(rolls.at[i, "roll_start"], utc=True)
            end = pd.to_datetime(rolls.at[i, "roll_end"], utc=True)
            i0 = max(0, ctx.calendar.searchsorted(start) - self.p["pre_days"])
            i1 = min(len(ctx.calendar), ctx.calendar.searchsorted(end, side="right"))
            # short the front (roll flow sells front): negative on the continuous proxy
            w.iloc[i0:i1, w.columns.get_loc(sym)] = -self.p["per_market"]
        return w
