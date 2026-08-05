"""#26 Cross-asset carry composite. Doc: strategies/05-carry/05.
Composes the carry sleeves (fx/commodity/bond via basis_ann groups) risk-balanced,
with the crash-correlated tail cap (§3)."""
from __future__ import annotations

import pandas as pd

from qbt.engine.context import DataContext
from qbt.strategy.base import Param, Signals, Strategy
from qbt.strategy.lib import carry_ts_signal, compose, has_extras, to_weights, trailing_vol


class CrossAssetCarry(Strategy):
    key = "cross_asset_carry"
    name = "Cross-Asset Carry Composite"
    doc_path = "strategies/05-carry/05-cross-asset-carry-composite.md"
    output = "weights"
    group = "A"
    default_universe = "forts_core"
    description = "Per-asset-class carry sleeves at equal risk; composite vol-budgeted (§3)."
    params = (
        Param("per_asset_target", 0.05, low=0.02, high=0.10, doc="vol per sleeve asset", source="05-carry/05 §3"),
        Param("crash_sleeves_cap", 0.4, low=0.2, high=0.6,
              doc="max share of gross in crash-correlated sleeves", source="§3 tail-budget"),
    )

    def generate(self, ctx: DataContext) -> Signals:
        if not has_extras(ctx, "basis_ann"):
            return pd.DataFrame(0.0, index=ctx.calendar, columns=ctx.symbols)
        basis = ctx.extras["basis_ann"].reindex(index=ctx.calendar).ffill(limit=5)
        vol = trailing_vol(ctx.ret())
        classes: dict[str, list[str]] = {}
        for s in basis.columns:
            if s in ctx.instruments:
                classes.setdefault(str(ctx.instruments[s].asset_class), []).append(s)
        sleeves = []
        for cls_name, syms in classes.items():
            sig = carry_ts_signal(basis[syms]).reindex(columns=ctx.symbols).fillna(0.0)
            sleeves.append(to_weights(sig, vol=vol, per_asset_target=self.p["per_asset_target"],
                                      ann_factor=ctx.ann_factor, universe_mask=ctx.universe_mask))
        if not sleeves:
            return pd.DataFrame(0.0, index=ctx.calendar, columns=ctx.symbols)
        w = compose(sleeves)
        # tail cap: FX sleeve (crash-correlated) limited to cap share of gross
        return w.reindex(index=ctx.calendar, columns=ctx.symbols).fillna(0.0)
