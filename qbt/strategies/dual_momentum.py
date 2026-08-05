"""#13 Dual momentum (GEM-style rotation). Doc: strategies/02-momentum/06.
MOEX menu: equity index / gold / cash-proxy bond instrument (first/second/third
universe symbols by convention; configure via universe yaml)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from qbt.engine.context import DataContext
from qbt.strategy.base import Param, Signals, Strategy


class DualMomentum(Strategy):
    key = "dual_momentum"
    name = "Dual Momentum (relative + absolute)"
    doc_path = "strategies/02-momentum/06-dual-momentum-asset-allocation.md"
    output = "weights"
    group = "A"
    default_universe = "dual_momentum_menu"
    description = ("Hold the strongest risk asset if its lookback return beats the cash proxy, "
                   "else the defensive asset (§3). Symbols: [risk..., defensive(last)].")
    params = (
        Param("lookback", 252, low=63, high=252, step=21, source="02-momentum/06 §3 (6-12m)"),
        Param("blend_lookbacks", True, choices=(True, False), doc="average 3/6/12m", source="§3"),
    )

    def generate(self, ctx: DataContext) -> Signals:
        tr = ctx.total_return
        if self.p["blend_lookbacks"]:
            mom = sum(tr.pct_change(lb, fill_method=None) for lb in (63, 126, 252)) / 3
        else:
            mom = tr.pct_change(self.p["lookback"], fill_method=None)
        risk_assets, defensive = ctx.symbols[:-1], ctx.symbols[-1]
        w = pd.DataFrame(0.0, index=ctx.calendar, columns=ctx.symbols)
        for t in ctx.rebalance_dates("ME"):
            if t not in mom.index:
                continue
            row = mom.loc[t, risk_assets].dropna()
            if not len(row):
                continue
            best = row.idxmax()
            w.loc[t, best if row.max() > 0 else defensive] = 1.0
        w = w.replace(0.0, np.nan).ffill().fillna(0.0)
        # exactly one holding per date: re-normalize forward-filled overlaps
        return w.div(w.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)
