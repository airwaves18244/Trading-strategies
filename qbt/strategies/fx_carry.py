"""#22 FX carry via FX-futures basis. Doc: strategies/05-carry/01.
On MOEX the tradable carry = the Si/Eu/CNY futures basis vs spot (forward discount).
Needs ctx.extras['basis_ann'] for FX symbols; degrades gracefully."""
from __future__ import annotations

import pandas as pd

from qbt.engine.context import DataContext
from qbt.strategy.base import Param, Signals, Strategy
from qbt.strategy.lib import carry_ts_signal, has_extras, to_weights, trailing_vol


class FxCarry(Strategy):
    key = "fx_carry"
    name = "FX Carry (futures basis)"
    doc_path = "strategies/05-carry/01-fx-carry.md"
    output = "weights"
    group = "A"
    default_universe = "forts_fx"
    description = "Position by sign/size of the FX futures basis vs hurdle; TS variant (§3)."
    params = (
        Param("hurdle_ann", 0.00, low=0.0, high=0.05, doc="carry hurdle", source="05-carry/01 §3"),
        Param("per_asset_target", 0.08, low=0.04, high=0.20),
        Param("risk_throttle", True, choices=(True, False),
              doc="halve exposure when trailing vol spikes (crash filter)", source="§3 refinement"),
    )

    def generate(self, ctx: DataContext) -> Signals:
        if not has_extras(ctx, "basis_ann"):
            return pd.DataFrame(0.0, index=ctx.calendar, columns=ctx.symbols)
        basis = ctx.extras["basis_ann"].reindex(index=ctx.calendar).ffill(limit=5)
        signal = carry_ts_signal(basis, hurdle_ann=self.p["hurdle_ann"])
        signal = signal.reindex(columns=ctx.symbols).fillna(0.0)
        vol = trailing_vol(ctx.ret())
        if self.p["risk_throttle"]:
            v5 = ctx.ret().rolling(5).std()
            v60 = ctx.ret().rolling(60).std()
            signal = signal.where(~(v5 > 1.5 * v60), signal * 0.5)
        return to_weights(signal, vol=vol, per_asset_target=self.p["per_asset_target"],
                          ann_factor=ctx.ann_factor, universe_mask=ctx.universe_mask)
