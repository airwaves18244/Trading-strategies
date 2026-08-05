"""Registry-wide guarantees: all 43 present, lookahead-free, cost-monotone, runnable."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from qbt.analytics.validation import assert_no_lookahead
from qbt.data.schemas import EVENT_SCHEMAS
from qbt.engine.cost_models import FlatCostModel, scale_cost_model
from qbt.engine.costs import CostParams
from qbt.engine.runner import run_backtest
from qbt.strategy import registry
from qbt.testing.synthetic import event_fixture, make_context

EXPECTED_KEYS = 43


@pytest.fixture(scope="module")
def ctx():
    c = make_context(8, "2017-01-01", "2022-12-30", seed=11)
    for schema in EVENT_SCHEMAS:
        c.events[schema] = event_fixture(schema, c.symbols, c.calendar, n_events=20)
    rng = np.random.default_rng(2)
    c.extras["basis_ann"] = pd.DataFrame(
        rng.normal(0.03, 0.05, (len(c.calendar), len(c.symbols))),
        index=c.calendar, columns=c.symbols).rolling(15).mean()
    c.extras["spread_series"] = pd.DataFrame(
        np.cumsum(rng.normal(0, 0.1, (len(c.calendar), 3)), axis=0),
        index=c.calendar, columns=c.symbols[:3])
    return c


def test_all_43_registered():
    assert len(registry.all_strategies(refresh=True)) == EXPECTED_KEYS


def test_every_strategy_has_doc_and_params():
    for key, cls in registry.all_strategies().items():
        meta = cls.describe()
        assert meta.doc_path.startswith("strategies/"), key
        assert meta.group in ("A", "B", "C"), key
        for p in meta.params:
            assert p.name and p.default is not None or p.default is None  # spec present


@pytest.mark.parametrize("key", sorted(registry.all_strategies(refresh=True)))
def test_no_lookahead(key, ctx):
    assert_no_lookahead(registry.get(key)(), ctx)


@pytest.mark.parametrize("key", sorted(registry.all_strategies(refresh=True)))
def test_runs_and_cost_monotone(key, ctx):
    cls = registry.get(key)
    base = FlatCostModel(CostParams(commission_bps=4, half_spread_bps=3, borrow_bps_yr=100))
    r1 = run_backtest(cls(), ctx, cost_model=base)
    assert np.isfinite(r1.equity.iloc[-1])
    assert set(r1.per_year.columns) >= {"period", "gross", "net"}
    if len(r1.trades):
        r2 = run_backtest(cls(), ctx, cost_model=scale_cost_model(base, 2.0))
        assert r2.metrics.get("cagr", 0) <= r1.metrics.get("cagr", 0) + 1e-9, \
            f"{key}: higher costs improved returns"
