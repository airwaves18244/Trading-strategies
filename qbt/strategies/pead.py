"""#31 Post-earnings announcement drift. Doc: strategies/07-event-driven/01.
Requires earnings_events (CSV schema). CAR3-based side when no consensus (§3-2)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from qbt.engine.context import DataContext
from qbt.strategy.base import Param, Signals, Strategy
from qbt.strategy.lib import event_weights


class Pead(Strategy):
    key = "pead"
    name = "Post-Earnings Announcement Drift"
    doc_path = "strategies/07-event-driven/01-post-earnings-announcement-drift.md"
    output = "weights"
    group = "B"
    data_requirements = ("earnings_events",)
    default_universe = "moex_liquid"
    description = "Drift after earnings surprises; SUE when consensus exists, else CAR3 sign (§3)."
    params = (
        Param("entry_lag", 2, low=1, high=5, doc="bars after announcement", source="07-…/01 §3 (day +2)"),
        Param("holding_bars", 60, low=20, high=90, source="§3 (60d / to next announcement)"),
        Param("weight_per_event", 0.02, low=0.005, high=0.05),
        Param("long_only", True, choices=(True, False), doc="short leg borrow-constrained"),
    )

    def generate(self, ctx: DataContext) -> Signals:
        ev = ctx.events["earnings_events"].copy()
        ts = pd.to_datetime(ev["report_ts"], utc=True)
        # side: SUE sign if consensus present, else CAR3 (market-adjusted 3-day reaction)
        if "eps_consensus" in ev.columns and ev["eps_consensus"].notna().any():
            surprise = ev["eps_actual"] - ev["eps_consensus"]
        else:
            surprise = pd.Series(np.nan, index=ev.index)
        r = ctx.ret()
        bench = r.mean(axis=1)
        sides = []
        for i in ev.index:
            s = surprise.loc[i]
            if pd.notna(s):
                sides.append(1 if s > 0 else -1)
                continue
            sym = ev.at[i, "symbol"]
            pos = ctx.calendar.searchsorted(ts.loc[i], side="right") - 1
            if sym in r.columns and 0 <= pos < len(ctx.calendar) - 1:
                sl = slice(pos, min(pos + 2, len(ctx.calendar)))
                car3 = float((r[sym].iloc[sl] - bench.iloc[sl]).sum())
                sides.append(1 if car3 > 0 else -1)
            else:
                sides.append(0)
        ev["side"] = sides
        if self.p["long_only"]:
            ev = ev[ev["side"] > 0]
        return event_weights(
            ev, ctx.calendar, ctx.symbols,
            entry_lag_bars=self.p["entry_lag"], holding_bars=self.p["holding_bars"],
            side="side", weight_per_event=self.p["weight_per_event"], date_col="report_ts",
        )
