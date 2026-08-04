"""Cost model contract. PHASE 0 CONTRACT.

Implementations (Flat, SqrtImpact, AlgopackSpread) live in qbt/engine/cost_models.py (WS-C).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

import pandas as pd


@dataclass(frozen=True)
class CostParams:
    commission_bps: float = 4.0        # MOEX retail broker ~0.04%
    exchange_fee_bps: float = 0.6
    half_spread_bps: float = 3.0       # default; per-instrument override / ALGOPACK-calibrated
    impact_coef_bps: float = 10.0      # bps at 100% ADV participation
    impact_exponent: float = 0.5       # sqrt impact law
    borrow_bps_yr: float = 300.0       # short borrow cost, annualized
    fixed_rub_per_trade: float = 0.0


@runtime_checkable
class CostModel(Protocol):
    params: CostParams

    def trade_cost_bps(
        self,
        traded_notional: pd.DataFrame,          # |Δposition| in currency, per (ts, symbol)
        adv_notional: pd.DataFrame | None,      # trailing ADV, same shape (None => no impact term)
        spread_bps: pd.DataFrame | None,        # per-instrument half-spread override
    ) -> pd.DataFrame: ...
    """Cost of trading, bps of traded notional, per (ts, symbol)."""

    def holding_cost_bps(
        self,
        positions_notional: pd.DataFrame,       # signed position notional per (ts, symbol)
    ) -> pd.DataFrame: ...
    """Daily holding cost (borrow on shorts), bps of |position|, per (ts, symbol)."""
