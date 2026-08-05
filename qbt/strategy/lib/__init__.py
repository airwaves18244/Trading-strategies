"""Family engines: thin, reusable building blocks for the 43 strategies."""
from qbt.strategy.lib.carry_curve import (
    annualized_basis, carry_ts_signal, carry_xs_signal, deseasonalized_slope,
    has_extras, slope_zscore, vix_style_basis,
)
from qbt.strategy.lib.event_study import car_table, event_dates, event_weights
from qbt.strategy.lib.overlay import VolTargetOverlay, compose
from qbt.strategy.lib.spread import SpreadTrader, half_life_ar1, hedge_ratio, pairs_weights
from qbt.strategy.lib.ts_signal import to_weights, trailing_vol, ts_ensemble
from qbt.strategy.lib.xs_rank import (
    cross_sectional_weights, rank_xs, skip_month_return, zscore_xs,
)

__all__ = [
    "annualized_basis", "carry_ts_signal", "carry_xs_signal", "deseasonalized_slope",
    "has_extras", "slope_zscore", "vix_style_basis",
    "car_table", "event_dates", "event_weights",
    "VolTargetOverlay", "compose",
    "SpreadTrader", "half_life_ar1", "hedge_ratio", "pairs_weights",
    "to_weights", "trailing_vol", "ts_ensemble",
    "cross_sectional_weights", "rank_xs", "skip_month_return", "zscore_xs",
]
