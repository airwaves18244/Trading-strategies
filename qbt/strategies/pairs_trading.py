"""#1 Pairs trading (distance + cointegration machinery). Doc: strategies/01-arbitrage-relative-value/01.

Default pair list = MOEX textbook pairs (§8 of the doc's recommendations);
override via the `pairs` param (comma-separated "A/B" pairs).
"""
from __future__ import annotations

from qbt.engine.context import DataContext
from qbt.strategy.base import Param, Signals, Strategy
from qbt.strategy.lib import pairs_weights

DEFAULT_PAIRS = "MOEX:SBER/MOEX:SBERP,MOEX:LKOH/MOEX:ROSN,MOEX:TATN/MOEX:TATNP,MOEX:GAZP/MOEX:NVTK"


class PairsTrading(Strategy):
    key = "pairs_trading"
    name = "Pairs Trading (z-score state machine)"
    doc_path = "strategies/01-arbitrage-relative-value/01-pairs-trading.md"
    output = "weights"
    group = "A"
    default_universe = "moex_liquid"
    description = "Beta-weighted pair spreads: enter |z|>2, exit |z|<0.5, stop |z|>4 (§3)."
    params = (
        Param("pairs", DEFAULT_PAIRS, doc="comma-separated SYM_A/SYM_B pairs"),
        Param("formation_bars", 252, low=126, high=756, step=21, source="01-…/01 §3"),
        Param("z_in", 2.0, low=1.5, high=2.5, step=0.25, source="§3 entry 1.5-2.5σ"),
        Param("z_out", 0.5, low=0.0, high=1.0, step=0.25, source="§3"),
        Param("z_stop", 4.0, low=3.0, high=5.0, step=0.5, source="§3 divergence stop"),
        Param("max_holding_bars", 126, low=42, high=252, step=21, source="§3 6m window"),
        Param("min_half_life", 5.0, low=2.0, high=10.0, source="§3 half-life 5-40d"),
        Param("max_half_life", 40.0, low=20.0, high=80.0, source="§3"),
        Param("gross", 1.0, low=0.2, high=2.0),
    )

    def generate(self, ctx: DataContext) -> Signals:
        pairs = []
        for chunk in str(self.p["pairs"]).split(","):
            a, _, b = chunk.strip().partition("/")
            if a in ctx.total_return.columns and b in ctx.total_return.columns:
                pairs.append((a, b))
        if not pairs:  # synthetic/test universes: fall back to first two symbols
            syms = ctx.symbols
            pairs = [(syms[0], syms[1])] if len(syms) >= 2 else []
        return pairs_weights(
            ctx.total_return, pairs, universe_mask=ctx.universe_mask,
            formation_bars=self.p["formation_bars"], z_in=self.p["z_in"],
            z_out=self.p["z_out"], z_stop=self.p["z_stop"],
            max_holding_bars=self.p["max_holding_bars"],
            min_half_life=self.p["min_half_life"], max_half_life=self.p["max_half_life"],
            gross=self.p["gross"],
        )
