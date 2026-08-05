"""#20 Swing pullback-in-trend. Doc: strategies/04-mean-reversion-swing/03."""
from __future__ import annotations

import numpy as np
import pandas as pd

from qbt.engine.context import DataContext
from qbt.strategy.base import OrderIntent, Param, Signals, Strategy
from qbt.strategies.breakout_channel import atr


class SwingPullback(Strategy):
    key = "swing_pullback"
    name = "Swing Pullback-in-Trend"
    doc_path = "strategies/04-mean-reversion-swing/03-swing-pullback-in-trend.md"
    output = "orders"
    group = "A"
    default_universe = "moex_liquid"
    description = ("Buy 1-2 ATR pullbacks in uptrends (price>200MA & 6m return>0); "
                   "stop under pullback low, 2R target, time stop (§3).")
    compatible_overlays = ()
    params = (
        Param("trend_ma", 200, low=100, high=250, step=10, source="04-…/03 §3"),
        Param("mom_window", 126, low=63, high=252, doc="medium-term return filter", source="§3"),
        Param("pullback_atr", 1.5, low=1.0, high=2.0, step=0.25, source="§3 (1-2 ATR)"),
        Param("stop_atr", 1.25, low=1.0, high=1.5, source="§3 (1-1.5 ATR)"),
        Param("target_r", 2.0, low=1.5, high=3.0, step=0.5, doc="take-profit in R", source="§3 (2-3R)"),
        Param("time_stop", 18, low=10, high=25, source="§3 (15-20d)"),
        Param("risk_frac", 0.005, low=0.0025, high=0.0075, source="§3 (0.25-0.75%)"),
    )

    def generate(self, ctx: DataContext) -> Signals:
        intents: list[OrderIntent] = []
        for sym in ctx.symbols:
            c, h, lo = ctx.close[sym], ctx.high[sym], ctx.low[sym]
            ma = c.rolling(self.p["trend_ma"], min_periods=self.p["trend_ma"] // 2).mean()
            mom = c.pct_change(self.p["mom_window"], fill_method=None)
            a = atr(h, lo, c, 20)
            swing_high = c.rolling(10, min_periods=5).max()
            pull = (swing_high - c) / a
            in_trend = (c > ma) & (mom > 0)
            trigger = in_trend & (pull >= self.p["pullback_atr"]) & (pull.shift(1) < self.p["pullback_atr"])
            for t in c.index[trigger.fillna(False)]:
                px, av = float(c.loc[t]), float(a.loc[t]) if np.isfinite(a.loc[t]) else None
                if not av:
                    continue
                stop = px - self.p["stop_atr"] * av
                take = px + self.p["target_r"] * (px - stop)
                intents.append(OrderIntent(
                    ts=t, symbol=sym, side=1, size_mode="risk_frac", size=self.p["risk_frac"],
                    stop=stop, take=take, time_stop_bars=self.p["time_stop"],
                    tag=f"pb:{sym}:{t.date()}",
                ))
        return intents
