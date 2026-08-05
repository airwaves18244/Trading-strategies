"""#3 Futures cash-and-carry basis. Doc: strategies/01-arbitrage-relative-value/03.
MOEX version: long spot equity / short its FORTS single-stock future when the
annualized basis clears the hurdle. Needs ctx.extras['basis_ann'] built from
spot vs futures pairs; symbol convention: basis column = spot symbol."""
from __future__ import annotations

import numpy as np
import pandas as pd

from qbt.engine.context import DataContext
from qbt.strategy.base import Param, Signals, Strategy
from qbt.strategy.lib import has_extras


class CashAndCarry(Strategy):
    key = "cash_and_carry"
    name = "Cash-and-Carry Basis"
    doc_path = "strategies/01-arbitrage-relative-value/03-futures-cash-and-carry-basis.md"
    output = "weights"
    group = "A"
    default_universe = "moex_liquid"
    description = "Long spot / short future when annualized basis > hurdle; hold to convergence (§3)."
    params = (
        Param("hurdle_ann", 0.05, low=0.02, high=0.10, doc="entry hurdle over cash yield",
              source="01-…/03 §3 (cash + 3-5%)"),
        Param("exit_ann", 0.01, low=0.0, high=0.03, doc="exit when basis compresses below"),
        Param("per_position", 0.10, low=0.02, high=0.25, doc="gross per basis position (both legs)"),
    )

    def generate(self, ctx: DataContext) -> Signals:
        w = pd.DataFrame(0.0, index=ctx.calendar, columns=ctx.symbols)
        if not has_extras(ctx, "basis_ann"):
            return w
        basis = ctx.extras["basis_ann"].reindex(index=ctx.calendar).ffill(limit=5)
        fut_map = ctx.extras.get("basis_future_map")   # {spot_symbol: future_symbol}
        per = self.p["per_position"] / 2
        for spot in basis.columns:
            if spot not in w.columns:
                continue
            fut = None
            if fut_map is not None and spot in getattr(fut_map, "columns", []):
                fut = str(fut_map[spot].iloc[0])
            b = basis[spot]
            state = pd.Series(0.0, index=ctx.calendar)
            on = False
            for t in ctx.calendar:
                v = b.get(t, np.nan)
                if not np.isfinite(v):
                    state[t] = per if on else 0.0
                    continue
                if not on and v > self.p["hurdle_ann"]:
                    on = True
                elif on and v < self.p["exit_ann"]:
                    on = False
                state[t] = per if on else 0.0
            w[spot] += state
            if fut and fut in w.columns:
                w[fut] -= state
        return w.where(ctx.universe_mask, 0.0)
