"""#24 Bond carry & roll-down (OFZ). Doc: strategies/05-carry/03.
Proxy: carry signal from OFZ index/futures term slope via ctx.extras['basis_ann']
(medium confidence per architecture map). Degrades gracefully."""
from __future__ import annotations

import pandas as pd

from qbt.engine.context import DataContext
from qbt.strategy.base import Param, Signals, Strategy
from qbt.strategy.lib import carry_ts_signal, has_extras, to_weights, trailing_vol


class BondCarry(Strategy):
    key = "bond_carry"
    name = "Bond Carry & Roll-Down (OFZ)"
    doc_path = "strategies/05-carry/03-bond-carry-rolldown.md"
    output = "weights"
    group = "A"
    default_universe = "moex_bonds"
    description = "Long duration when carry+rolldown positive vs funding; DV01-risk sized (§3)."
    params = (
        Param("hurdle_ann", 0.0, low=0.0, high=0.03, source="05-carry/03 §3"),
        Param("per_asset_target", 0.06, low=0.03, high=0.15),
    )

    def generate(self, ctx: DataContext) -> Signals:
        if not has_extras(ctx, "basis_ann"):
            return pd.DataFrame(0.0, index=ctx.calendar, columns=ctx.symbols)
        basis = ctx.extras["basis_ann"].reindex(index=ctx.calendar).ffill(limit=5)
        signal = carry_ts_signal(basis, hurdle_ann=self.p["hurdle_ann"])
        signal = signal.reindex(columns=ctx.symbols).fillna(0.0)
        vol = trailing_vol(ctx.ret())
        return to_weights(signal, vol=vol, per_asset_target=self.p["per_asset_target"],
                          ann_factor=ctx.ann_factor, universe_mask=ctx.universe_mask)
