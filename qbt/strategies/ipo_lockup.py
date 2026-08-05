"""#34 IPO lockup expiry. Doc: strategies/07-event-driven/04.
Requires ipo_lockups. Order strategy: short into expiry with a squeeze stop (§3-A),
optional post-overhang long (§3-B)."""
from __future__ import annotations

import pandas as pd

from qbt.engine.context import DataContext
from qbt.strategy.base import OrderIntent, Param, Signals, Strategy


class IpoLockup(Strategy):
    key = "ipo_lockup"
    name = "IPO Lockup Expiry"
    doc_path = "strategies/07-event-driven/04-ipo-lockup-expiry.md"
    output = "orders"
    group = "B"
    data_requirements = ("ipo_lockups",)
    default_universe = "moex_liquid"
    description = "Short 5-10d before lockup expiry, exit after; squeeze stop +10% (§3-A)."
    params = (
        Param("entry_days_before", 7, low=3, high=10, source="07-…/04 §3 (5-10d)"),
        Param("exit_days_after", 3, low=1, high=8, source="§3 (+2..+5)"),
        Param("stop_pct", 0.10, low=0.05, high=0.15, doc="adverse move stop", source="§3"),
        Param("risk_frac", 0.004, low=0.001, high=0.01, source="§3 (0.3-0.5% per event)"),
        Param("reversion_leg", False, choices=(True, False), source="§3-B"),
    )

    def generate(self, ctx: DataContext) -> Signals:
        ev = ctx.events["ipo_lockups"]
        intents: list[OrderIntent] = []
        cal = ctx.calendar
        for i in ev.index:
            sym = ev.at[i, "symbol"]
            if sym not in ctx.close.columns:
                continue
            expiry = pd.to_datetime(ev.at[i, "lockup_expiry"], utc=True)
            pos = cal.searchsorted(expiry, side="left")
            entry_pos = pos - self.p["entry_days_before"]
            if entry_pos < 1 or pos >= len(cal):
                continue
            t = cal[entry_pos - 1]              # signal bar; engine enters next open
            px = float(ctx.close.iloc[entry_pos - 1][sym])
            if not pd.notna(px) or px <= 0:
                continue
            hold = self.p["entry_days_before"] + self.p["exit_days_after"]
            intents.append(OrderIntent(
                ts=t, symbol=sym, side=-1, size_mode="risk_frac",
                size=self.p["risk_frac"], stop=px * (1 + self.p["stop_pct"]),
                time_stop_bars=hold, tag=f"lockup:{sym}:{expiry.date()}",
            ))
            if self.p["reversion_leg"] and pos + 5 < len(cal):
                t2 = cal[pos + 4]
                px2 = float(ctx.close.iloc[pos + 4][sym]) if pd.notna(ctx.close.iloc[pos + 4][sym]) else None
                if px2:
                    intents.append(OrderIntent(
                        ts=t2, symbol=sym, side=1, size_mode="risk_frac",
                        size=self.p["risk_frac"], stop=px2 * 0.85,
                        time_stop_bars=60, tag=f"lockup-rev:{sym}:{expiry.date()}",
                    ))
        return intents
