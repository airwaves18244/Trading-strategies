"""#33 Buybacks & insider buying. Doc: strategies/07-event-driven/03.
Requires insider_buyback_events; long-tilted multi-month holds."""
from __future__ import annotations

from qbt.engine.context import DataContext
from qbt.strategy.base import Param, Signals, Strategy
from qbt.strategy.lib import event_weights


class BuybackInsider(Strategy):
    key = "buyback_insider"
    name = "Buybacks & Insider Buying"
    doc_path = "strategies/07-event-driven/03-buybacks-and-insider-buying.md"
    output = "weights"
    group = "B"
    data_requirements = ("insider_buyback_events",)
    default_universe = "moex_liquid"
    description = "Long companies after buyback announcements / clustered insider buys (§3)."
    params = (
        Param("entry_lag", 2, low=1, high=5, source="07-…/03 §3 (day +2)"),
        Param("holding_bars", 126, low=63, high=252, source="§3 (6-12m)"),
        Param("weight_per_event", 0.03, low=0.01, high=0.05),
        Param("min_pct_of_shares", 0.0, low=0.0, high=10.0,
              doc="buyback size floor, % of shares (0 = no filter)", source="§3 (≥5% strong)"),
    )

    def generate(self, ctx: DataContext) -> Signals:
        ev = ctx.events["insider_buyback_events"].copy()
        if self.p["min_pct_of_shares"] > 0 and "pct_of_shares" in ev.columns:
            is_bb = ev["kind"].astype(str) == "buyback"
            ev = ev[~is_bb | (ev["pct_of_shares"].fillna(0) >= self.p["min_pct_of_shares"])]
        return event_weights(
            ev, ctx.calendar, ctx.symbols,
            entry_lag_bars=self.p["entry_lag"], holding_bars=self.p["holding_bars"],
            side=1, weight_per_event=self.p["weight_per_event"], date_col="event_date",
        )
