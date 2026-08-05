"""#4 ETF-NAV arbitrage (stress-discount reversion). Doc: strategies/01-arbitrage-relative-value/04.
Group C: needs nav_series (P and NAV per fund). Data-gated — runs on synthetic fixtures."""
from __future__ import annotations

import numpy as np
import pandas as pd

from qbt.engine.context import DataContext
from qbt.strategy.base import Param, Signals, Strategy


class EtfNavArbitrage(Strategy):
    key = "etf_nav_arbitrage"
    name = "ETF-NAV Stress-Discount Reversion"
    doc_path = "strategies/01-arbitrage-relative-value/04-etf-nav-arbitrage.md"
    output = "weights"
    group = "C"
    data_requirements = ("nav_series",)
    default_universe = "moex_etf"
    description = "Long funds at z<-2.5 discount vs own history AND discount <-1% (§3-A)."
    params = (
        Param("z_entry", -2.5, low=-3.0, high=-2.0, source="01-…/04 §3-A"),
        Param("abs_discount", -0.01, low=-0.03, high=-0.005, source="§3-A"),
        Param("z_exit", 0.0, low=-0.5, high=0.5, source="§3-A"),
        Param("z_window", 252, low=126, high=504),
        Param("time_stop_bars", 63, low=21, high=90, source="§3-A (1-3m)"),
        Param("per_position", 0.04, low=0.01, high=0.05, source="§3 (2-5% NAV)"),
    )

    def generate(self, ctx: DataContext) -> Signals:
        nav = ctx.events["nav_series"]
        w = pd.DataFrame(0.0, index=ctx.calendar, columns=ctx.symbols)
        win, per = self.p["z_window"], self.p["per_position"]
        for sym, g in nav.groupby("symbol"):
            if sym not in w.columns or sym not in ctx.close.columns:
                continue
            n = g.sort_values("date").set_index("date")["nav"]
            n.index = pd.to_datetime(n.index, utc=True)
            n = n.reindex(ctx.calendar).ffill()
            d = ctx.close[sym] / n - 1.0
            mu = d.rolling(win, min_periods=win // 4).mean().shift(1)
            sd = d.rolling(win, min_periods=win // 4).std().shift(1)
            z = ((d - mu) / sd).replace([np.inf, -np.inf], np.nan)
            state, held = np.zeros(len(z)), 0
            zv, dv = z.to_numpy(), d.to_numpy()
            for t in range(1, len(zv)):
                if state[t - 1] == 0:
                    if np.isfinite(zv[t]) and zv[t] < self.p["z_entry"] and dv[t] < self.p["abs_discount"]:
                        state[t], held = per, 0
                else:
                    held += 1
                    exit_ = (np.isfinite(zv[t]) and zv[t] >= self.p["z_exit"]) or held >= self.p["time_stop_bars"]
                    state[t] = 0.0 if exit_ else state[t - 1]
            w[sym] = state
        return w.where(ctx.universe_mask, 0.0)
