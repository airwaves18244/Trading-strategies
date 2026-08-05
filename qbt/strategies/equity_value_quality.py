"""#36 Cross-sectional equity value + quality. Doc: strategies/08-value-fundamental-factor/01.
Requires fundamentals_pit (as-of dated). Composite value z + profitability z double sort (§3)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from qbt.engine.context import DataContext
from qbt.strategy.base import Param, Signals, Strategy
from qbt.strategy.lib import cross_sectional_weights, zscore_xs


class EquityValueQuality(Strategy):
    key = "equity_value_quality"
    name = "Equity Value + Quality (double sort)"
    doc_path = "strategies/08-value-fundamental-factor/01-cross-sectional-equity-value.md"
    output = "weights"
    group = "B"
    data_requirements = ("fundamentals_pit",)
    default_universe = "moex_liquid"
    description = "Cheap-and-profitable composite: E/P + B/P value z-avg with GP/quality z (§3)."
    params = (
        Param("value_weight", 0.6, low=0.3, high=0.8, doc="value vs quality blend", source="08-…/01 §3"),
        Param("top_frac", 0.2, low=0.1, high=0.3),
        Param("long_only", True, choices=(True, False)),
        Param("sector_neutral", True, choices=(True, False), source="§3"),
        Param("staleness_bars", 252, low=126, high=378, doc="drop fundamentals older than this"),
    )

    def _metric_frame(self, ev: pd.DataFrame, metric: str, ctx: DataContext) -> pd.DataFrame:
        """Point-in-time frame of the latest known metric value per (date, symbol)."""
        sub = ev[ev["metric"].astype(str) == metric]
        out = pd.DataFrame(np.nan, index=ctx.calendar, columns=ctx.symbols)
        for sym, g in sub.groupby("symbol"):
            if sym not in out.columns:
                continue
            s = g.sort_values("asof_date").set_index("asof_date")["value"]
            s.index = pd.to_datetime(s.index, utc=True)
            aligned = s.reindex(out.index.union(s.index)).ffill(limit=self.p["staleness_bars"])
            out[sym] = aligned.reindex(out.index)
        return out

    def generate(self, ctx: DataContext) -> Signals:
        ev = ctx.events["fundamentals_pit"]
        eps = self._metric_frame(ev, "eps", ctx)
        book = self._metric_frame(ev, "book", ctx)
        gp = self._metric_frame(ev, "gross_profit", ctx)
        px = ctx.close
        value = zscore_xs(eps / px).fillna(0.0) * 0.5 + zscore_xs(book / px).fillna(0.0) * 0.5
        quality = (zscore_xs(gp / book.replace(0, np.nan)).fillna(0.0)
                   if gp.notna().any().any() else value * 0.0)
        vw = self.p["value_weight"]
        signal = (vw * value + (1 - vw) * quality).where(value != 0.0)  # NaN when no data at all
        sector_map = {s: (i.sector or "NA") for s, i in ctx.instruments.items()}
        return cross_sectional_weights(
            signal, ctx.universe_mask,
            top_frac=self.p["top_frac"], bottom_frac=self.p["top_frac"],
            long_only=self.p["long_only"],
            sector_map=sector_map, sector_neutral=self.p["sector_neutral"],
            rebalance_dates=ctx.rebalance_dates("ME"), min_names=2,
        )
