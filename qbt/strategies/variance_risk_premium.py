"""#27 Variance risk premium harvesting. Doc: strategies/06-volatility/01.
Requires options_surface. MVP expression: VRP estimate (ATM IV − realized-vol
forecast) gates a short-vol proxy position; full delta-hedged book is post-MVP."""
from __future__ import annotations

import numpy as np
import pandas as pd

from qbt.engine.context import DataContext
from qbt.strategy.base import Param, Signals, Strategy


class VarianceRiskPremium(Strategy):
    key = "variance_risk_premium"
    name = "Variance Risk Premium (IV-RV gate)"
    doc_path = "strategies/06-volatility/01-variance-risk-premium.md"
    output = "weights"
    group = "B"
    data_requirements = ("options_surface",)
    default_universe = "vol_futures"
    description = "Short vol proxy only when ATM IV exceeds realized-vol forecast by margin (§3)."
    params = (
        Param("vrp_min", 0.02, low=0.0, high=0.06, doc="min IV-RV gap (vol pts) to be short",
              source="06-…/01 §3 (skip entries when VRP<=0)"),
        Param("rv_window", 21, low=10, high=63, doc="realized vol forecast window (EWMA)"),
        Param("size", 0.08, low=0.02, high=0.15),
    )

    def generate(self, ctx: DataContext) -> Signals:
        surf = ctx.events["options_surface"].copy()
        surf["date"] = pd.to_datetime(surf["date"], utc=True)
        # ATM proxy: per date, median IV of nearest-expiry options
        atm = (surf.sort_values(["date", "expiry"])
               .groupby("date")
               .apply(lambda g: g[g["expiry"] == g["expiry"].min()]["iv"].median(),
                      include_groups=False))
        atm = atm.reindex(ctx.calendar).ffill(limit=5)
        underlying = ctx.symbols[0]
        r = ctx.close[underlying].pct_change(fill_method=None)
        rv = (r.pow(2).ewm(halflife=self.p["rv_window"]).mean() * ctx.ann_factor) ** 0.5
        vrp = (atm - rv.shift(1)).astype(float)          # strictly trailing RV
        w = pd.DataFrame(0.0, index=ctx.calendar, columns=ctx.symbols)
        w[underlying] = np.where(vrp > self.p["vrp_min"], -self.p["size"], 0.0)
        return w
