"""Analytic engine tests: closed-form answers on synthetic data."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from qbt.engine.costs import CostParams
from qbt.engine.cost_models import FlatCostModel, SqrtImpactCostModel, load_cost_preset, scale_cost_model
from qbt.engine.runner import run_backtest
from qbt.strategy.base import OrderIntent, Param, Strategy
from qbt.testing.synthetic import (
    bid_ask_bounce_context, constant_drift_context, known_drawdown_context, make_context,
)

ZERO_COSTS = FlatCostModel(CostParams(commission_bps=0, exchange_fee_bps=0,
                                      half_spread_bps=0, borrow_bps_yr=0))


class BuyHold(Strategy):
    key = "_test_bh"
    name = "bh"
    doc_path = ""
    output = "weights"

    def generate(self, ctx):
        return pd.DataFrame(1.0, index=ctx.calendar, columns=ctx.symbols)


class Reversal1D(Strategy):
    key = "_test_rev"
    name = "rev"
    doc_path = ""
    output = "weights"
    params = (Param("lag_mode", 0),)

    def generate(self, ctx):
        r = ctx.close.pct_change(fill_method=None)
        sig = -np.sign(r)
        return sig.fillna(0.0)


def test_buy_and_hold_closed_form():
    ctx = constant_drift_context(0.001, 300)
    res = run_backtest(BuyHold(), ctx, cost_model=ZERO_COSTS, lag=1)
    assert res.equity.iloc[-1] == pytest.approx((1.001) ** 299, rel=1e-10)


def test_cost_doubling_doubles_commission_line():
    ctx = make_context(3, "2020-01-01", "2021-12-31", seed=5)
    base = FlatCostModel(CostParams(commission_bps=4, exchange_fee_bps=0,
                                    half_spread_bps=0, borrow_bps_yr=0))
    r1 = run_backtest(Reversal1D(), ctx, cost_model=base)
    r2 = run_backtest(Reversal1D(), ctx, cost_model=scale_cost_model(base, 2.0))
    c1, c2 = r1.costs["commission"].sum(), r2.costs["commission"].sum()
    assert c2 == pytest.approx(2 * c1, rel=1e-9)
    assert r2.metrics["sharpe"] <= r1.metrics["sharpe"] + 1e-9


def test_lag_canary_bid_ask_bounce():
    """Reversal on trade prints (deterministic alternator): executing on the
    signal bar's close (lag=1 in close-to-close convention) still captures the
    bounce -> fake alpha; the Gatev one-day-wait (skip a bar, lag=2) kills it.
    Doc 01-…/01 §7: waiting must destroy a large share of gross 'profit'."""
    ctx = bid_ask_bounce_context(half_spread=0.005, n_days=750)
    r1 = run_backtest(Reversal1D(), ctx, cost_model=ZERO_COSTS, lag=1)
    r2 = run_backtest(Reversal1D(), ctx, cost_model=ZERO_COSTS, lag=2)
    assert r1.metrics["sharpe"] > 3.0                       # bounce-contaminated
    assert r2.metrics["sharpe"] < 0.5                       # one-day-wait kills it


def test_known_drawdown_metrics():
    ctx, expected = known_drawdown_context()
    res = run_backtest(BuyHold(), ctx, cost_model=ZERO_COSTS, lag=0)
    exact = {"max_dd", "dd_duration_days", "total_return"}
    for k, v in expected.items():
        if k in res.metrics and np.isfinite(v):
            # statistical metrics: fixture counts the flat first bar, the engine
            # drops the leading NaN return -> n=549 vs 550; allow 0.5% for those
            rel = 1e-6 if k in exact else 5e-3
            assert res.metrics[k] == pytest.approx(v, rel=rel, abs=1e-9), k


def test_order_engine_conservative_fills():
    """Stop and take both inside one bar => stop fills."""
    cal = pd.bdate_range("2020-01-01", periods=10, tz="UTC")
    close = pd.DataFrame({"A": [100, 100, 100, 100, 100, 100, 100, 100, 100, 100]},
                         index=cal, dtype=float)
    high = close + 10
    low = close - 10
    open_ = close.copy()
    from qbt.engine.context import DataContext
    from qbt.core.types import Instrument, AssetClass
    ctx = DataContext(calendar=cal, instruments={"A": Instrument(symbol="A", exchange="X",
                      asset_class=AssetClass.EQUITY)}, open=open_, high=high, low=low,
                      close=close, total_return=close, volume=close * 0 + 1e6,
                      value=close * 1e6, universe_mask=close.astype(bool))

    class OneShot(Strategy):
        key = "_test_os"
        name = "os"
        doc_path = ""
        output = "orders"

        def generate(self, c):
            return [OrderIntent(ts=cal[1], symbol="A", side=1, size_mode="nav_frac",
                                size=0.5, stop=95.0, take=105.0, time_stop_bars=5)]

    res = run_backtest(OneShot(), ctx, cost_model=ZERO_COSTS)
    exits = res.trades[res.trades.reason != "entry"]
    assert list(exits.reason) == ["stop"]
    assert exits.iloc[0].price == pytest.approx(95.0)


def test_risk_frac_sizing():
    cal = pd.bdate_range("2020-01-01", periods=6, tz="UTC")
    px = pd.DataFrame({"A": [100.0] * 6}, index=cal)
    from qbt.engine.context import DataContext
    from qbt.core.types import Instrument, AssetClass
    ctx = DataContext(calendar=cal, instruments={"A": Instrument(symbol="A", exchange="X",
                      asset_class=AssetClass.EQUITY)}, open=px, high=px, low=px, close=px,
                      total_return=px, volume=px * 0 + 1e6, value=px * 1e6,
                      universe_mask=px.astype(bool))

    class OneShot(Strategy):
        key = "_test_rf"
        name = "rf"
        doc_path = ""
        output = "orders"

        def generate(self, c):
            return [OrderIntent(ts=cal[0], symbol="A", side=1, size_mode="risk_frac",
                                size=0.01, stop=90.0, time_stop_bars=3)]

    res = run_backtest(OneShot(), ctx, cost_model=ZERO_COSTS, initial_nav=1.0)
    entry = res.trades.iloc[0]
    # qty = NAV*0.01 / |100-90| = 0.001 units
    assert entry.qty == pytest.approx(0.001, rel=1e-9)
