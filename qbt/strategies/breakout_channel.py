"""#16 Breakout/channel trend (Donchian/Turtle-style). Doc: strategies/03-trend-following/02.
Order strategy: N-day-high breakout entries, ATR stop, channel trailing via time/stop exits."""
from __future__ import annotations

import numpy as np
import pandas as pd

from qbt.engine.context import DataContext
from qbt.strategy.base import OrderIntent, Param, Signals, Strategy


def atr(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 20) -> pd.Series:
    tr = pd.concat([high - low, (high - close.shift(1)).abs(),
                    (low - close.shift(1)).abs()], axis=1).max(axis=1)
    return tr.rolling(window, min_periods=window // 2).mean()


class BreakoutChannel(Strategy):
    key = "breakout_channel"
    name = "Breakout / Channel Trend (Donchian)"
    doc_path = "strategies/03-trend-following/02-breakout-channel-trend.md"
    output = "orders"
    group = "A"
    default_universe = "forts_core"
    description = "Long N-day-high breach with 2·ATR stop, exit opposite N/2 channel or time (§3)."
    compatible_overlays = ()      # order strategy; sizing embedded
    params = (
        Param("channel", 55, low=20, high=100, step=5, doc="breakout lookback",
              source="03-…/02 §3 (20/55 classic)"),
        Param("atr_mult", 2.0, low=1.5, high=3.0, step=0.25, source="§3 (1.5-3 ATR stop)"),
        Param("risk_frac", 0.0075, low=0.0025, high=0.01, doc="NAV risked per breakout",
              source="§3 (0.5-1%)"),
        Param("max_hold", 120, low=40, high=250, doc="time stop, bars"),
        Param("both_sides", True, choices=(True, False), doc="short breakdowns too"),
    )

    def generate(self, ctx: DataContext) -> Signals:
        intents: list[OrderIntent] = []
        n = self.p["channel"]
        for sym in ctx.symbols:
            c, h, lo = ctx.close[sym], ctx.high[sym], ctx.low[sym]
            a = atr(h, lo, c, 20)
            hi_n = c.rolling(n, min_periods=n).max().shift(1)
            lo_n = c.rolling(n, min_periods=n).min().shift(1)
            long_sig = (c > hi_n) & (c.shift(1) <= hi_n.shift(1))
            short_sig = (c < lo_n) & (c.shift(1) >= lo_n.shift(1)) if self.p["both_sides"] else pd.Series(False, index=c.index)
            for t in c.index[long_sig.fillna(False)]:
                px, av = float(c.loc[t]), float(a.loc[t]) if np.isfinite(a.loc[t]) else None
                if av:
                    intents.append(OrderIntent(ts=t, symbol=sym, side=1, size_mode="risk_frac",
                                               size=self.p["risk_frac"], stop=px - self.p["atr_mult"] * av,
                                               time_stop_bars=self.p["max_hold"], tag=f"bo:{sym}:{t.date()}"))
            for t in c.index[short_sig.fillna(False)]:
                px, av = float(c.loc[t]), float(a.loc[t]) if np.isfinite(a.loc[t]) else None
                if av:
                    intents.append(OrderIntent(ts=t, symbol=sym, side=-1, size_mode="risk_frac",
                                               size=self.p["risk_frac"], stop=px + self.p["atr_mult"] * av,
                                               time_stop_bars=self.p["max_hold"], tag=f"bd:{sym}:{t.date()}"))
        return intents
