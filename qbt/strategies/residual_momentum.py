"""#10 Residual (idiosyncratic) momentum. Doc: strategies/02-momentum/03.

Residuals vs the equal-weight universe return (single-factor market model,
rolling beta) — the FF3 version needs factor data unavailable on MOEX; the
market-residual variant preserves the doc's core claim (§3 minimum: market).
Signal = mean(residual)/std(residual) over t-12..t-2 (the IR scaling of §3).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from qbt.engine.context import DataContext
from qbt.strategy.base import Param, Signals, Strategy
from qbt.strategy.lib import cross_sectional_weights


class ResidualMomentum(Strategy):
    key = "residual_momentum"
    name = "Residual (Idiosyncratic) Momentum"
    doc_path = "strategies/02-momentum/03-residual-idiosyncratic-momentum.md"
    output = "weights"
    group = "A"
    default_universe = "moex_liquid"
    description = "Momentum on market-residual returns, IR-scaled (§3); ~half the crash risk."
    params = (
        Param("beta_window", 504, low=252, high=756, step=126,
              doc="rolling beta estimation window", source="02-momentum/03 §3 (24-60m)"),
        Param("formation", 231, low=126, high=252, doc="residual momentum window (t-12..t-2)",
              source="02-momentum/03 §3"),
        Param("skip", 21, low=0, high=42, doc="skip window"),
        Param("top_frac", 0.1, low=0.05, high=0.3),
        Param("long_only", True, choices=(True, False)),
    )

    def generate(self, ctx: DataContext) -> Signals:
        r = ctx.ret()
        mkt = r.where(ctx.universe_mask).mean(axis=1)
        bw = self.p["beta_window"]
        cov = r.rolling(bw, min_periods=bw // 2).cov(mkt)
        var = mkt.rolling(bw, min_periods=bw // 2).var()
        beta = cov.div(var, axis=0)
        resid = r - beta.shift(1).mul(mkt, axis=0)          # lagged beta: strictly trailing
        f, sk = self.p["formation"], self.p["skip"]
        mean = resid.shift(sk).rolling(f, min_periods=f // 2).mean()
        std = resid.shift(sk).rolling(f, min_periods=f // 2).std()
        signal = (mean / std).replace([np.inf, -np.inf], np.nan)
        return cross_sectional_weights(
            signal, ctx.universe_mask,
            top_frac=self.p["top_frac"], bottom_frac=self.p["top_frac"],
            long_only=self.p["long_only"], rebalance_dates=ctx.rebalance_dates("ME"),
        )
