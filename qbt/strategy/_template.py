"""Template for `qbt new-strategy <name>`.

Checklist:
  1. Rename the class and set `key` (snake_case, unique) and `name`.
  2. Point `doc_path` at your strategy note (or a corpus doc under strategies/).
  3. Pick `output`: "weights" (target-weight matrix) or "orders" (OrderIntent list).
  4. Set `group`: "A" (runs on MOEX data), "B" (needs a CSV event schema —
     declare it in `data_requirements`), "C" (data-gated).
  5. Declare every tunable as a Param with low/high range and a `source` ref.
  6. generate() must be strictly trailing: a value at t may only use data <= t.
     The runner applies the execution lag on top — do not pre-shift.
  7. Test: the registry auto-discovers this file; run
     `pytest tests/strategies -k <key>` and the global lookahead harness.
"""
from __future__ import annotations

import pandas as pd

from qbt.engine.context import DataContext
from qbt.strategy.base import Param, Signals, Strategy
from qbt.strategy.lib import cross_sectional_weights, skip_month_return


class MyStrategy(Strategy):
    key = "my_strategy"                       # TODO: unique snake_case key
    name = "My Strategy"                      # TODO: human name for the UI
    doc_path = "strategies/02-momentum/01-cross-sectional-equity-momentum.md"  # TODO
    output = "weights"
    group = "A"
    default_universe = "moex_liquid"
    description = "TODO: one-line description shown in the terminal."
    params = (
        Param("formation", 252, low=126, high=378, step=21,
              doc="lookback bars for the signal", source="02-momentum/01 §3"),
        Param("top_frac", 0.2, low=0.05, high=0.5,
              doc="fraction of universe held long", source="02-momentum/01 §3"),
    )

    def generate(self, ctx: DataContext) -> Signals:
        signal = skip_month_return(ctx.total_return, formation=self.p["formation"],
                                   skip=21, bars_per_month=1)  # params in bars
        return cross_sectional_weights(
            signal, ctx.universe_mask,
            top_frac=self.p["top_frac"], bottom_frac=self.p["top_frac"],
            long_only=True,
            rebalance_dates=ctx.rebalance_dates("ME"),
        )
