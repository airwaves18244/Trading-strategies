"""#7 Convertible bond arbitrage. Doc: strategies/01-arbitrage-relative-value/07.
Group C (convert_terms + bond marks). MVP: cheapness proxy = bond price vs
parity (conversion_ratio × equity); long cheap convert / short delta equity."""
from __future__ import annotations

import numpy as np
import pandas as pd

from qbt.engine.context import DataContext
from qbt.strategy.base import Param, Signals, Strategy


class ConvertibleArbitrage(Strategy):
    key = "convertible_arbitrage"
    name = "Convertible Arbitrage (parity-cheapness)"
    doc_path = "strategies/01-arbitrage-relative-value/07-convertible-bond-arbitrage.md"
    output = "weights"
    group = "C"
    data_requirements = ("convert_terms",)
    default_universe = "moex_liquid"
    description = "Long converts cheap to parity+floor proxy, short delta of the equity (§3)."
    params = (
        Param("cheapness_min", 0.02, low=0.01, high=0.06, doc="min discount to proxy value",
              source="01-…/07 §3 (2-4%)"),
        Param("delta", 0.6, low=0.3, high=0.9, doc="hedge delta (flat proxy; model post-MVP)"),
        Param("per_name", 0.03, low=0.01, high=0.05, source="§3 (≤2-3%)"),
    )

    def generate(self, ctx: DataContext) -> Signals:
        terms = ctx.events["convert_terms"]
        w = pd.DataFrame(0.0, index=ctx.calendar, columns=ctx.symbols)
        for i in terms.index:
            bond, eq = terms.at[i, "bond_symbol"], terms.at[i, "equity_symbol"]
            ratio = float(terms.at[i, "conversion_ratio"])
            if bond not in ctx.close.columns or eq not in ctx.close.columns or ratio <= 0:
                continue
            parity = ctx.close[eq] * ratio
            proxy_value = np.maximum(parity, 100.0 * 0.9)     # crude bond-floor proxy
            cheap = (proxy_value / ctx.close[bond] - 1.0).shift(1)   # trailing
            on = (cheap > self.p["cheapness_min"]).fillna(False)
            w[bond] += np.where(on, self.p["per_name"], 0.0)
            w[eq] -= np.where(on, self.p["per_name"] * self.p["delta"], 0.0)
        return w.where(ctx.universe_mask, 0.0)
