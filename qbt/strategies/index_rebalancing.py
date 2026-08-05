"""#32 Index add/delete rebalancing (deletion-reversion variant). Doc: strategies/07-event-driven/02.
Requires index_events. Trades the SURVIVING pocket: long deletions at effective
date, hold for the reversion window (§3-A). Addition front-running is dead (§2)."""
from __future__ import annotations

from qbt.engine.context import DataContext
from qbt.strategy.base import Param, Signals, Strategy
from qbt.strategy.lib import event_weights


class IndexRebalancing(Strategy):
    key = "index_rebalancing"
    name = "Index Rebalancing (deletion reversion)"
    doc_path = "strategies/07-event-driven/02-index-rebalancing.md"
    output = "weights"
    group = "B"
    data_requirements = ("index_events",)
    default_universe = "moex_liquid"
    description = "Long index deletions at effective date; forced-flow overshoot reverts (§3-A)."
    params = (
        Param("holding_bars", 40, low=20, high=60, source="07-…/02 §3-A (20-60d)"),
        Param("weight_per_event", 0.03, low=0.01, high=0.05),
        Param("trade_additions", False, choices=(True, False),
              doc="research-only: the addition premium is documented dead", source="§2/§4"),
    )

    def generate(self, ctx: DataContext) -> Signals:
        ev = ctx.events["index_events"].copy()
        ev["side"] = 0
        ev.loc[ev["action"].astype(str) == "delete", "side"] = 1
        if self.p["trade_additions"]:
            ev.loc[ev["action"].astype(str) == "add", "side"] = 1
        ev = ev[ev["side"] != 0]
        return event_weights(
            ev, ctx.calendar, ctx.symbols,
            entry_lag_bars=0, holding_bars=self.p["holding_bars"],
            side="side", weight_per_event=self.p["weight_per_event"],
            date_col="effective_date",
        )
