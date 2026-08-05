"""#5 Merger arbitrage. Doc: strategies/01-arbitrage-relative-value/05.
Requires deals. Cash deals only in the MVP (stock-deal short leg needs borrow);
hurdle-based selection with tail exclusion (§3)."""
from __future__ import annotations

import pandas as pd

from qbt.engine.context import DataContext
from qbt.strategy.base import OrderIntent, Param, Signals, Strategy


class MergerArbitrage(Strategy):
    key = "merger_arbitrage"
    name = "Merger (Risk) Arbitrage — cash deals"
    doc_path = "strategies/01-arbitrage-relative-value/05-merger-arbitrage.md"
    output = "orders"
    group = "B"
    data_requirements = ("deals",)
    default_universe = "moex_liquid"
    description = "Long targets of definitive cash deals when annualized spread clears hurdle (§3)."
    params = (
        Param("hurdle_ann", 0.06, low=0.03, high=0.12, doc="annualized spread hurdle over cash",
              source="01-…/05 §3 (cash yield + 3-6%)"),
        Param("tail_ann", 0.30, low=0.20, high=0.50, doc="exclude spreads above (priced break risk)",
              source="§3 (25-30%)"),
        Param("risk_frac", 0.008, low=0.002, high=0.02, doc="NAV risked per deal at downside",
              source="§3 (0.5-1%)"),
        Param("expected_days", 120, low=60, high=250, doc="baseline days-to-close estimate"),
    )

    def generate(self, ctx: DataContext) -> Signals:
        deals = ctx.events["deals"]
        intents: list[OrderIntent] = []
        cal = ctx.calendar
        for i in deals.index:
            sym = deals.at[i, "target_symbol"]
            if sym not in ctx.close.columns:
                continue
            ann_ts = pd.to_datetime(deals.at[i, "announce_date"], utc=True)
            offer = float(deals.at[i, "offer_price"])
            pos = cal.searchsorted(ann_ts, side="right")           # signal next bar
            if pos + 1 >= len(cal) or offer <= 0:
                continue
            px = ctx.close.iloc[pos][sym]
            if not pd.notna(px) or px <= 0 or px >= offer:
                continue
            spread = offer / float(px) - 1.0
            days = self.p["expected_days"]
            if pd.notna(deals.at[i, "close_date"] if "close_date" in deals.columns else None):
                d = (pd.to_datetime(deals.at[i, "close_date"], utc=True) - ann_ts).days
                days = max(20, d)
            s_ann = spread * 365.0 / days
            if not (self.p["hurdle_ann"] <= s_ann <= self.p["tail_ann"]):
                continue
            downside = 0.20                                        # unaffected-price fall assumption
            hold = min(int(days * 252 / 365) + 10, len(cal) - pos - 1)
            intents.append(OrderIntent(
                ts=cal[pos], symbol=sym, side=1, size_mode="risk_frac",
                size=self.p["risk_frac"], stop=float(px) * (1 - downside),
                take=offer, time_stop_bars=hold,
                tag=f"deal:{sym}:{ann_ts.date()}",
            ))
        return intents
