"""#35 Macro-announcement drift. Doc: strategies/07-event-driven/05.
Requires macro_calendar. Variant A (announcement-day premium harvest): long the
benchmark-proxy instrument only around scheduled announcements."""
from __future__ import annotations

import pandas as pd

from qbt.engine.context import DataContext
from qbt.strategy.base import Param, Signals, Strategy


class MacroAnnouncement(Strategy):
    key = "macro_announcement"
    name = "Macro Announcement-Day Premium"
    doc_path = "strategies/07-event-driven/05-macro-announcement-drift.md"
    output = "weights"
    group = "B"
    data_requirements = ("macro_calendar",)
    default_universe = "moex_index"
    description = "Hold index exposure only on scheduled macro-announcement days (§3-A)."
    params = (
        Param("days_before", 1, low=0, high=2, doc="enter N bars before release", source="07-…/05 §3"),
        Param("days_after", 0, low=0, high=2, doc="stay N bars after release"),
        Param("kinds", "cbr_rate,cpi", doc="comma-separated event kinds to trade"),
        Param("exposure", 1.0, low=0.1, high=1.5),
    )

    def generate(self, ctx: DataContext) -> Signals:
        ev = ctx.events["macro_calendar"]
        kinds = {k.strip() for k in str(self.p["kinds"]).split(",") if k.strip()}
        ts = pd.to_datetime(ev["release_ts"], utc=True)
        sel = ev["kind"].astype(str).isin(kinds) if kinds else pd.Series(True, index=ev.index)
        w = pd.DataFrame(0.0, index=ctx.calendar, columns=ctx.symbols)
        target = ctx.symbols[0]  # index-proxy instrument = first universe symbol
        for t in ts[sel]:
            if not len(ctx.calendar) or t > ctx.calendar[-1]:
                continue  # scheduled beyond data end
            pos = ctx.calendar.searchsorted(t, side="left")
            lo = max(0, pos - self.p["days_before"])
            hi = min(len(ctx.calendar), pos + self.p["days_after"] + 1)
            w.iloc[lo:hi, w.columns.get_loc(target)] = self.p["exposure"]
        return w
