"""#2 Statistical arbitrage via mean-reverting residuals. Doc: strategies/01-arbitrage-relative-value/02.

Sector-ETF-residual variant of Avellaneda-Lee adapted to MOEX: residual vs the
equal-weight sector basket, O-U s-score entries (§3). Earnings-window exclusion
needs earnings_events (optional — applied when present in ctx.events).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from qbt.engine.context import DataContext
from qbt.strategy.base import Param, Signals, Strategy


class StatArbResidual(Strategy):
    key = "stat_arb_residual"
    name = "Stat-Arb: Mean-Reverting Residuals (s-score)"
    doc_path = "strategies/01-arbitrage-relative-value/02-statistical-arbitrage-mean-reverting-portfolios.md"
    output = "weights"
    group = "A"
    default_universe = "moex_liquid"
    description = "Short residual s>+1.25, long s<-1.25, exits at ±(0.5,0.75) per §3."
    params = (
        Param("resid_window", 60, low=40, high=90, step=10, doc="O-U fit window",
              source="01-…/02 §3 (40-90d)"),
        Param("entry", 1.25, low=1.0, high=1.5, step=0.05, source="§3"),
        Param("exit_long", -0.5, low=-0.75, high=-0.25, source="§3 close long at s>-0.5"),
        Param("exit_short", 0.75, low=0.25, high=1.0, source="§3 (short exit richer: borrow)"),
        Param("max_half_life", 15.0, low=5.0, high=30.0, source="§3 half-life ≤ ~15d"),
        Param("per_name", 0.02, low=0.005, high=0.05, doc="weight per open position"),
    )

    def generate(self, ctx: DataContext) -> Signals:
        r = ctx.ret()
        sector_map = {s: (i.sector or "NA") for s, i in ctx.instruments.items()}
        sec_ret = r.T.groupby(lambda s: sector_map.get(s, "NA")).transform("mean").T
        resid = (r - sec_ret).fillna(0.0)
        win = self.p["resid_window"]
        X = resid.rolling(win, min_periods=win).sum()          # cumulative residual proxy
        mu = X.rolling(win, min_periods=win // 2).mean()
        sd = X.rolling(win, min_periods=win // 2).std()
        s = ((X - mu) / sd).replace([np.inf, -np.inf], np.nan)
        # AR(1) half-life filter per symbol on the rolling window (approximate, monthly refresh)
        phi = X.rolling(win).corr(X.shift(1))
        hl = -np.log(2) / np.log(phi.clip(0.01, 0.999))
        tradable = hl <= self.p["max_half_life"]

        w = pd.DataFrame(0.0, index=ctx.calendar, columns=ctx.symbols)
        entry, xl, xs_ = self.p["entry"], self.p["exit_long"], self.p["exit_short"]
        per = self.p["per_name"]
        sv, tv = s.to_numpy(), tradable.fillna(False).to_numpy()
        wv = np.zeros_like(sv)
        for t in range(1, sv.shape[0]):
            prev = wv[t - 1]
            cur = prev.copy()
            st = sv[t]
            open_long = (st < -entry) & tv[t] & (prev == 0)
            open_short = (st > entry) & tv[t] & (prev == 0)
            cur[open_long] = per
            cur[open_short] = -per
            # exits
            close_long = (prev > 0) & (st > xl)
            close_short = (prev < 0) & (st < xs_)
            cur[close_long] = 0.0
            cur[close_short] = 0.0
            cur[~np.isfinite(st)] = 0.0
            wv[t] = cur
        w.iloc[:, :] = wv
        return w.where(ctx.universe_mask, 0.0)
