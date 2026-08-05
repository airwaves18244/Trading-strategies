"""#29 Volatility dispersion (index vs constituents). Doc: strategies/06-volatility/03.
Group C (needs per-constituent options surfaces). MVP: implied-correlation proxy
from index IV vs mean constituent IV gates a realized-dispersion position."""
from __future__ import annotations

import numpy as np
import pandas as pd

from qbt.engine.context import DataContext
from qbt.strategy.base import Param, Signals, Strategy


class Dispersion(Strategy):
    key = "dispersion"
    name = "Dispersion (implied-correlation gate)"
    doc_path = "strategies/06-volatility/03-dispersion-index-vs-constituents.md"
    output = "weights"
    group = "C"
    data_requirements = ("options_surface",)
    default_universe = "moex_liquid"
    description = ("Short index vol / long constituent vol proxy when implied correlation "
                   "is in its upper quantiles (§3). Data-gated: per-name surfaces required.")
    params = (
        Param("corr_quantile", 0.7, low=0.5, high=0.9, doc="entry when ρ_imp above this trailing quantile",
              source="06-…/03 §3 (60-80th pct)"),
        Param("size", 0.05, low=0.02, high=0.10),
        Param("quantile_window", 252, low=126, high=504),
    )

    def generate(self, ctx: DataContext) -> Signals:
        surf = ctx.events["options_surface"].copy()
        surf["date"] = pd.to_datetime(surf["date"], utc=True)
        w = pd.DataFrame(0.0, index=ctx.calendar, columns=ctx.symbols)
        if "underlying_symbol" not in surf.columns or surf["underlying_symbol"].isna().all():
            return w                                        # cannot split index vs names
        idx_sym = ctx.symbols[0]
        idx_iv = (surf[surf["underlying_symbol"] == idx_sym].groupby("date")["iv"].median()
                  .reindex(ctx.calendar).ffill(limit=5))
        name_iv = (surf[surf["underlying_symbol"] != idx_sym].groupby("date")["iv"].median()
                   .reindex(ctx.calendar).ffill(limit=5))
        rho_proxy = (idx_iv / name_iv).clip(0, 2)           # rising => correlation expensive
        q = rho_proxy.rolling(self.p["quantile_window"], min_periods=63)\
            .quantile(self.p["corr_quantile"]).shift(1)
        on = rho_proxy > q
        # proxy book: short index / long equal-weight constituents (vol legs unavailable in MVP)
        others = [s for s in ctx.symbols[1:]]
        w[idx_sym] = np.where(on, -self.p["size"], 0.0)
        if others:
            per = self.p["size"] / len(others)
            for s in others:
                w[s] = np.where(on, per, 0.0)
        return w
