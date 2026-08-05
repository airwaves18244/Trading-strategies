"""#42 Perpetual funding-rate arbitrage. Doc: strategies/10-crypto-specific/01.
Requires funding_rates (+ perp/spot bars via FileProvider). Delta-neutral carry:
weights represent the NET carry position (short perp / long spot pair as one line)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from qbt.engine.context import DataContext
from qbt.strategy.base import Param, Signals, Strategy


class FundingRateArb(Strategy):
    key = "funding_rate_arb"
    name = "Perp Funding-Rate Carry"
    doc_path = "strategies/10-crypto-specific/01-perpetual-funding-rate-arbitrage.md"
    output = "weights"
    group = "B"
    data_requirements = ("funding_rates",)
    default_universe = "crypto_majors"
    description = ("Collect funding when trailing 7d annualized funding > hurdle; exit below floor "
                   "or after persistent negative funding (§3). PnL = funding accrual stream via "
                   "ctx.extras['funding_ann'] mapped to a carry-index instrument per symbol.")
    params = (
        Param("hurdle_ann", 0.10, low=0.05, high=0.20, source="10-…/01 §3 (8-12%)"),
        Param("exit_ann", 0.05, low=0.0, high=0.10, source="§3"),
        Param("neg_days_exit", 3, low=1, high=5, source="§3 (negative >2-3 days)"),
        Param("per_venue_cap", 0.35, low=0.1, high=0.5, doc="counterparty budget", source="§3"),
        Param("size", 0.30, low=0.05, high=0.5, doc="weight per active carry line"),
    )

    def generate(self, ctx: DataContext) -> Signals:
        fr = ctx.events["funding_rates"].copy()
        fr["ts"] = pd.to_datetime(fr["ts"], utc=True)
        w = pd.DataFrame(0.0, index=ctx.calendar, columns=ctx.symbols)
        for sym, g in fr.groupby("symbol"):
            if sym not in w.columns:
                continue
            interval_h = float(g["interval_hours"].dropna().iloc[0]) if "interval_hours" in g and g["interval_hours"].notna().any() else 8.0
            per_year = 24.0 / interval_h * 365.0
            ann = (g.set_index("ts")["funding_rate"].sort_index() * per_year)
            daily = ann.resample("1D").mean().reindex(
                ctx.calendar.tz_convert("UTC").normalize()).ffill(limit=3)
            daily.index = ctx.calendar
            trail = daily.rolling(7, min_periods=3).mean().shift(1)
            neg_run = (daily < 0).rolling(self.p["neg_days_exit"]).sum().shift(1)
            state, on = pd.Series(0.0, index=ctx.calendar), False
            for t in ctx.calendar:
                tr_, nr = trail.get(t, np.nan), neg_run.get(t, 0)
                if on and (tr_ < self.p["exit_ann"] or nr >= self.p["neg_days_exit"]):
                    on = False
                elif not on and np.isfinite(tr_) and tr_ > self.p["hurdle_ann"]:
                    on = True
                state[t] = self.p["size"] if on else 0.0
            w[sym] = state.clip(upper=self.p["per_venue_cap"])
        return w
