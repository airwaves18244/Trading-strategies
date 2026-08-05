"""#11 Industry & factor momentum. Doc: strategies/02-momentum/04.

MOEX variant: industry momentum over sector groups (from Instrument.sector);
each sector basket = equal-weight members. Factor momentum needs a factor
library — represented here by the industry sleeve (§3-A); §3-B noted as a
future extension once factor returns exist in ctx.extras["factor_returns"].
"""
from __future__ import annotations

import pandas as pd

from qbt.engine.context import DataContext
from qbt.strategy.base import Param, Signals, Strategy


class IndustryFactorMomentum(Strategy):
    key = "industry_factor_momentum"
    name = "Industry Momentum (sector rotation)"
    doc_path = "strategies/02-momentum/04-industry-and-factor-momentum.md"
    output = "weights"
    group = "A"
    default_universe = "moex_liquid"
    description = "Long recent-winner sectors / short losers via member baskets (§3-A)."
    params = (
        Param("formation", 126, low=63, high=252, step=21,
              doc="sector momentum lookback", source="02-momentum/04 §3 (3-12m)"),
        Param("top_n", 3, low=1, high=5, step=1, doc="sectors held long"),
        Param("long_only", True, choices=(True, False)),
    )

    def generate(self, ctx: DataContext) -> Signals:
        sector_map = {s: (i.sector or "NA") for s, i in ctx.instruments.items()}
        sectors = sorted(set(sector_map.values()))
        member = {sec: [s for s, g in sector_map.items() if g == sec and s in ctx.total_return.columns]
                  for sec in sectors}
        tr = ctx.total_return
        sec_ret = pd.DataFrame({sec: tr[m].pct_change(fill_method=None).mean(axis=1)
                                for sec, m in member.items() if m})
        mom = (1 + sec_ret).rolling(self.p["formation"], min_periods=self.p["formation"] // 2)\
            .apply(lambda x: x.prod() - 1, raw=True)
        w = pd.DataFrame(0.0, index=ctx.calendar, columns=ctx.symbols)
        top_n = int(self.p["top_n"])
        for t in ctx.rebalance_dates("ME"):
            if t not in mom.index:
                continue
            row = mom.loc[t].dropna()
            if len(row) < max(2, top_n):
                continue
            winners = row.nlargest(top_n).index
            losers = row.nsmallest(top_n).index if not self.p["long_only"] else []
            picks = [(sec, 1.0) for sec in winners] + [(sec, -1.0) for sec in losers]
            for sec, sign in picks:
                names = [s for s in member.get(sec, []) if ctx.universe_mask.at[t, s]]
                if not names:
                    continue
                per = sign / (top_n * len(names)) * (1.0 if self.p["long_only"] else 0.5)
                w.loc[t, names] = per
        w = w.replace(0.0, pd.NA).ffill().fillna(0.0)
        return w.where(ctx.universe_mask, 0.0)
