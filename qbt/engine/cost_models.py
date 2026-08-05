"""Concrete cost models implementing the frozen `qbt.engine.costs.CostModel` protocol.

All three models return **bps of traded notional** from ``trade_cost_bps`` and
**bps of |position| per bar** from ``holding_cost_bps``, exactly as the protocol
specifies. They additionally expose ``trade_cost_components()`` (not part of the
frozen protocol) so the engines can fill the per-day ``COST_COLUMNS`` breakdown;
engines fall back to a single "commission" bucket for third-party models that
only implement the protocol.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

from qbt.core.errors import ConfigError
from qbt.engine.costs import CostModel, CostParams

__all__ = [
    "FlatCostModel", "SqrtImpactCostModel", "AlgopackSpreadCostModel",
    "load_cost_params", "load_cost_preset", "scale_cost_model",
    "COST_PRESET_DIR", "available_cost_presets", "trade_cost_components",
]

#: repo-root/configs/costs
COST_PRESET_DIR = Path(__file__).resolve().parents[2] / "configs" / "costs"

#: friendly YAML aliases -> CostParams field names
_ALIASES = {
    "commission": "commission_bps",
    "exchange_fee": "exchange_fee_bps",
    "half_spread": "half_spread_bps",
    "spread": "half_spread_bps",
    "impact": "impact_coef_bps",
    "impact_coef": "impact_coef_bps",
    "exponent": "impact_exponent",
    "borrow": "borrow_bps_yr",
    "borrow_bps": "borrow_bps_yr",
    "fixed_rub": "fixed_rub_per_trade",
}

_BARS_PER_YEAR = 252.0


def _zeros_like(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(0.0, index=df.index, columns=df.columns)


def _spread_frame(model: "FlatCostModel", traded: pd.DataFrame,
                  spread_bps: pd.DataFrame | None) -> pd.DataFrame:
    """Half-spread in bps, per (ts, symbol), with per-instrument override."""
    base = pd.DataFrame(float(model.params.half_spread_bps),
                        index=traded.index, columns=traded.columns)
    override = model.spread_bps_frame if model.spread_bps_frame is not None else spread_bps
    if override is not None:
        ov = override.reindex(index=traded.index, columns=traded.columns).astype(float)
        base = ov.where(ov.notna(), base)
    return base


@dataclass
class FlatCostModel:
    """Commission + exchange fee + half spread. No market impact.

    The model every analytic cost test uses: cost is a constant bps of traded
    notional, so doubling the parameters doubles the cost line exactly.
    """

    params: CostParams = field(default_factory=CostParams)
    #: optional per-instrument half-spread override frame (bps)
    spread_bps_frame: pd.DataFrame | None = None

    name: str = "flat"

    # ---------------- protocol ----------------

    def trade_cost_bps(
        self,
        traded_notional: pd.DataFrame,
        adv_notional: pd.DataFrame | None,
        spread_bps: pd.DataFrame | None,
    ) -> pd.DataFrame:
        comp = self.trade_cost_components(traded_notional, adv_notional, spread_bps)
        total = None
        for df in comp.values():
            total = df if total is None else total + df
        return _zeros_like(traded_notional) if total is None else total

    def holding_cost_bps(self, positions_notional: pd.DataFrame) -> pd.DataFrame:
        """Borrow accrual on shorts, bps of |position| per bar."""
        daily = float(self.params.borrow_bps_yr) / _BARS_PER_YEAR
        short = positions_notional.astype(float) < 0.0
        return _zeros_like(positions_notional).mask(short, daily)

    # ---------------- breakdown (engine extension) ----------------

    def _impact_bps(self, traded_notional: pd.DataFrame,
                    adv_notional: pd.DataFrame | None) -> pd.DataFrame:
        return _zeros_like(traded_notional)

    def trade_cost_components(
        self,
        traded_notional: pd.DataFrame,
        adv_notional: pd.DataFrame | None = None,
        spread_bps: pd.DataFrame | None = None,
    ) -> dict[str, pd.DataFrame]:
        traded = traded_notional.astype(float)
        commission = pd.DataFrame(
            float(self.params.commission_bps) + float(self.params.exchange_fee_bps),
            index=traded.index, columns=traded.columns,
        )
        if self.params.fixed_rub_per_trade:
            notional = traded.abs()
            per_trade = pd.DataFrame(
                np.where(notional.to_numpy() > 0.0,
                         float(self.params.fixed_rub_per_trade) * 1e4
                         / np.where(notional.to_numpy() > 0.0, notional.to_numpy(), 1.0),
                         0.0),
                index=traded.index, columns=traded.columns,
            )
            commission = commission + per_trade
        traded_zero = traded.abs() <= 0.0
        commission = commission.mask(traded_zero, 0.0)
        spread = _spread_frame(self, traded, spread_bps).mask(traded_zero, 0.0)
        impact = self._impact_bps(traded, adv_notional).mask(traded_zero, 0.0)
        return {"commission": commission, "spread": spread, "impact": impact}


@dataclass
class SqrtImpactCostModel(FlatCostModel):
    """Default model: flat costs plus ``impact_coef_bps * (traded/ADV)^exponent``.

    ``adv_notional=None`` (or a missing/non-positive ADV cell) skips the impact
    term rather than blowing up — synthetic contexts and thin names must still
    run.
    """

    name: str = "sqrt_impact"

    def _impact_bps(self, traded_notional: pd.DataFrame,
                    adv_notional: pd.DataFrame | None) -> pd.DataFrame:
        traded = traded_notional.astype(float)
        if adv_notional is None or float(self.params.impact_coef_bps) == 0.0:
            return _zeros_like(traded)
        adv = adv_notional.reindex(index=traded.index, columns=traded.columns).astype(float)
        a = adv.to_numpy()
        t = np.abs(traded.to_numpy())
        ok = np.isfinite(a) & (a > 0.0)
        participation = np.zeros_like(t)
        np.divide(t, a, out=participation, where=ok)
        participation = np.where(ok, participation, 0.0)
        bps = float(self.params.impact_coef_bps) * np.power(
            participation, float(self.params.impact_exponent))
        return pd.DataFrame(bps, index=traded.index, columns=traded.columns)


@dataclass
class AlgopackSpreadCostModel(SqrtImpactCostModel):
    """Sqrt-impact model whose half-spread comes from an ALGOPACK-calibrated frame.

    ``spread_bps_frame`` is (ts x symbol) *half*-spread in bps; cells that are
    missing fall back to ``params.half_spread_bps``.
    """

    name: str = "algopack_spread"

    def __init__(self, params: CostParams | None = None,
                 spread_bps_frame: pd.DataFrame | None = None):
        if spread_bps_frame is None:
            raise ValueError("AlgopackSpreadCostModel requires a spread_bps_frame")
        super().__init__(params=params or CostParams(), spread_bps_frame=spread_bps_frame)
        self.name = "algopack_spread"


# --------------------------------------------------------------------------- #
# presets                                                                      #
# --------------------------------------------------------------------------- #

def available_cost_presets() -> list[str]:
    if not COST_PRESET_DIR.is_dir():
        return []
    return sorted(p.stem for p in COST_PRESET_DIR.glob("*.yaml"))


def load_cost_params(name: str | Path) -> CostParams:
    """Read ``configs/costs/<name>.yaml`` into :class:`CostParams`."""
    path = Path(name)
    if not path.suffix:
        path = COST_PRESET_DIR / f"{name}.yaml"
    if not path.is_file():
        raise ConfigError(
            f"Unknown cost preset '{name}'. Available: {available_cost_presets()}")
    blob: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    fields = set(CostParams.__dataclass_fields__)
    kwargs: dict[str, float] = {}
    for key, value in blob.items():
        field_name = _ALIASES.get(str(key), str(key))
        if field_name in fields:
            kwargs[field_name] = float(value)
    return CostParams(**kwargs)


def load_cost_preset(name: str | Path = "moex_equity", model: str = "sqrt_impact") -> CostModel:
    """Build the default cost model for a named preset."""
    params = load_cost_params(name)
    cls = {"flat": FlatCostModel, "sqrt_impact": SqrtImpactCostModel}.get(model)
    if cls is None:
        raise ConfigError(f"unknown cost model kind {model!r}")
    out = cls(params=params)
    out.name = f"{Path(str(name)).stem}:{model}"
    return out


def scale_cost_model(model: CostModel, mult: float) -> CostModel:
    """Return a copy of ``model`` with every cost parameter multiplied by ``mult``.

    Used by ``analytics.validation.cost_sensitivity``. ``impact_exponent`` is a
    shape parameter, not a cost level, and is deliberately left alone.
    """
    p = model.params
    scaled = replace(
        p,
        commission_bps=p.commission_bps * mult,
        exchange_fee_bps=p.exchange_fee_bps * mult,
        half_spread_bps=p.half_spread_bps * mult,
        impact_coef_bps=p.impact_coef_bps * mult,
        borrow_bps_yr=p.borrow_bps_yr * mult,
        fixed_rub_per_trade=p.fixed_rub_per_trade * mult,
    )
    frame = getattr(model, "spread_bps_frame", None)
    if isinstance(model, AlgopackSpreadCostModel):
        out: CostModel = AlgopackSpreadCostModel(
            params=scaled, spread_bps_frame=None if frame is None else frame * mult)
    else:
        out = type(model)(params=scaled,
                          spread_bps_frame=None if frame is None else frame * mult)
    out.name = f"{getattr(model, 'name', type(model).__name__)}x{mult:g}"
    return out


def trade_cost_components(
    model: CostModel,
    traded_notional: pd.DataFrame,
    adv_notional: pd.DataFrame | None,
    spread_bps: pd.DataFrame | None,
) -> dict[str, pd.DataFrame]:
    """Per-component bps breakdown, with a protocol-only fallback.

    Models that do not implement the (non-frozen) ``trade_cost_components``
    extension get their whole cost reported under "commission".
    """
    fn = getattr(model, "trade_cost_components", None)
    if callable(fn):
        return fn(traded_notional, adv_notional, spread_bps)
    total = model.trade_cost_bps(traded_notional, adv_notional, spread_bps)
    return {"commission": total,
            "spread": _zeros_like(total),
            "impact": _zeros_like(total)}
