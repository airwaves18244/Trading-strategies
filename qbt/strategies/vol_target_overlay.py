"""#30 Volatility-targeting overlay + demo strategy. Doc: strategies/06-volatility/04.
The Overlay itself lives in qbt.strategy.lib.overlay.VolTargetOverlay (runner option
`overlay=`). This module registers the demo standalone: vol-targeted index exposure."""
from __future__ import annotations

import numpy as np
import pandas as pd

from qbt.engine.context import DataContext
from qbt.strategy.base import Param, Signals, Strategy
from qbt.strategy.lib import VolTargetOverlay


class VolTargetIndex(Strategy):
    key = "vol_target_overlay"
    name = "Vol-Targeted Index Exposure (overlay demo)"
    doc_path = "strategies/06-volatility/04-volatility-targeting-overlay.md"
    output = "weights"
    group = "A"
    default_universe = "moex_index"
    description = "Buy-and-hold index scaled by target/realized vol — the overlay as a strategy (§3)."
    params = (
        Param("target", 0.10, low=0.05, high=0.20, doc="annualized vol target",
              source="06-…/04 §3"),
        Param("halflife", 20, low=10, high=60, source="§3 (EWMA λ≈0.94 ≈ hl 20)"),
        Param("cap", 1.5, low=1.0, high=2.0, source="§3 (cap 1.5-2.0)"),
        Param("floor", 0.3, low=0.1, high=0.5, source="§3"),
    )

    def generate(self, ctx: DataContext) -> Signals:
        base = pd.DataFrame(0.0, index=ctx.calendar, columns=ctx.symbols)
        base[ctx.symbols[0]] = 1.0
        ov = VolTargetOverlay(target=self.p["target"], halflife=self.p["halflife"],
                              cap=self.p["cap"], floor=self.p["floor"],
                              ann_factor=ctx.ann_factor)
        return ov.transform(base, ctx)
