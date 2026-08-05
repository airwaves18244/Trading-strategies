"""#19 Index panic mean-reversion. Doc: strategies/04-mean-reversion-swing/02."""
from __future__ import annotations

import numpy as np
import pandas as pd

from qbt.engine.context import DataContext
from qbt.strategy.base import OrderIntent, Param, Signals, Strategy


class IndexPanicReversion(Strategy):
    key = "index_panic_reversion"
    name = "Index Panic Mean-Reversion"
    doc_path = "strategies/04-mean-reversion-swing/02-index-panic-mean-reversion.md"
    output = "orders"
    group = "A"
    default_universe = "moex_index"
    description = ("Long index after multi-day -kσ selloff WITH vol spike; disaster stop, "
                   "time exit (§3). Deliberately counter-cyclical — no vol-target overlay.")
    compatible_overlays = ()      # §3: buys vol spikes; wrapping defeats the design
    params = (
        Param("ret_window", 5, low=3, high=5, doc="selloff measurement window", source="04-…/02 §3"),
        Param("ret_sigma", 1.5, low=1.0, high=2.5, step=0.25, doc="selloff threshold in σ", source="§3"),
        Param("vol_mult", 1.5, low=1.2, high=2.0, doc="5d vol > mult × 60d vol", source="§3"),
        Param("risk_frac", 0.02, low=0.01, high=0.03, doc="NAV risked at disaster stop", source="§3 (1-3%)"),
        Param("stop_sigma", 2.0, low=1.5, high=3.0, doc="disaster stop distance, σ of window", source="§3"),
        Param("time_stop", 12, low=8, high=15, doc="bars", source="§3 (10-15d)"),
        Param("cooldown", 5, low=0, high=10, doc="bars between entries"),
    )

    def generate(self, ctx: DataContext) -> Signals:
        sym = ctx.symbols[0]
        c = ctx.close[sym]
        r = c.pct_change(fill_method=None)
        sigma60 = r.rolling(60, min_periods=30).std()
        win = self.p["ret_window"]
        ret_w = c.pct_change(win, fill_method=None)
        thresh = -self.p["ret_sigma"] * sigma60 * np.sqrt(win)
        v5, v60 = r.rolling(5).std(), sigma60
        panic = (ret_w < thresh) & (v5 > self.p["vol_mult"] * v60)
        intents: list[OrderIntent] = []
        last_entry = -10**9
        idx = ctx.calendar
        pv, cv, sv = panic.fillna(False).to_numpy(), c.to_numpy(), (sigma60 * np.sqrt(win)).to_numpy()
        for i in range(len(idx)):
            if pv[i] and i - last_entry > self.p["cooldown"]:
                px = float(cv[i])
                stop = px * (1 - self.p["stop_sigma"] * float(sv[i])) if np.isfinite(sv[i]) else px * 0.9
                intents.append(OrderIntent(
                    ts=idx[i], symbol=sym, side=1, size_mode="risk_frac",
                    size=self.p["risk_frac"], stop=stop,
                    time_stop_bars=self.p["time_stop"], tag=f"panic:{idx[i].date()}",
                ))
                last_entry = i
        return intents
