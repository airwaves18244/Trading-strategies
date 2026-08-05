"""#43 Cross-exchange spot arbitrage (non-HFT census variant). Doc: strategies/10-crypto-specific/02.
Group C: needs multi_venue_quotes. Positions when net spread exceeds fees+threshold;
this is an opportunity-census research strategy, not an execution simulator."""
from __future__ import annotations

import numpy as np
import pandas as pd

from qbt.engine.context import DataContext
from qbt.strategy.base import Param, Signals, Strategy


class CrossExchangeArb(Strategy):
    key = "cross_exchange_arb"
    name = "Cross-Exchange Spot Arbitrage (census)"
    doc_path = "strategies/10-crypto-specific/02-cross-exchange-spot-arbitrage.md"
    output = "weights"
    group = "C"
    data_requirements = ("multi_venue_quotes",)
    default_universe = "crypto_majors"
    description = "Long cheap-venue/short rich-venue when net spread > fees + threshold (§3)."
    params = (
        Param("min_spread_bps", 30.0, low=10.0, high=100.0, source="10-…/02 §3 (30-50bp majors)"),
        Param("fees_bps", 20.0, low=5.0, high=50.0, doc="round-trip taker fees both venues"),
        Param("size", 0.10, low=0.02, high=0.25),
        Param("max_hold_bars", 5, low=1, high=20),
    )

    def generate(self, ctx: DataContext) -> Signals:
        q = ctx.events["multi_venue_quotes"].copy()
        q["ts"] = pd.to_datetime(q["ts"], utc=True)
        q["mid"] = (q["bid"] + q["ask"]) / 2
        w = pd.DataFrame(0.0, index=ctx.calendar, columns=ctx.symbols)
        thresh = (self.p["min_spread_bps"] + self.p["fees_bps"]) / 1e4
        for sym, g in q.groupby("symbol"):
            if sym not in w.columns:
                continue
            piv = g.pivot_table(index="ts", columns="venue", values="mid")
            if piv.shape[1] < 2:
                continue
            daily = piv.resample("1D").last().reindex(
                ctx.calendar.tz_convert("UTC").normalize()).ffill(limit=2)
            daily.index = ctx.calendar
            spread = (daily.max(axis=1) / daily.min(axis=1) - 1.0).shift(1)   # trailing signal
            sig = (spread > thresh).astype(float)
            # cap holding: rolling window so stale dislocations don't pin exposure
            held = sig.rolling(self.p["max_hold_bars"], min_periods=1).max()
            w[sym] = held * self.p["size"]
        return w
