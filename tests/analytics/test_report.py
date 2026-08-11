"""run.json v2 report blocks — hand-computable fixtures (WS-A, docs/ui-upgrade.md §1).

Every expectation here is either arithmetic done by hand in the test body or a
numpy recomputation; nothing asserts against the implementation's own output.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

from qbt.analytics.metrics import per_year_table, summary
from qbt.analytics.report import (
    attribution_rows, benchmark_stats, drawdown_rows, is_oos_sharpe, monthly_table,
    rolling_stats, trade_stats,
)
from qbt.engine.portfolio import exposure_frame
from qbt.engine.result import COST_COLUMNS, TRADES_COLUMNS, BacktestResult, RunMeta

V2_KEYS = ("benchmark_stats", "monthly", "drawdowns", "rolling", "attribution", "trade_stats")
V1_KEYS = ("meta", "metrics", "equity", "equity_gross", "drawdown", "benchmark",
           "exposure", "per_year", "costs_total", "trades", "n_trades")


def _idx(dates: list[str]) -> pd.DatetimeIndex:
    return pd.DatetimeIndex([pd.Timestamp(d, tz="UTC") for d in dates])


def _ledger(rows: list[tuple[str, str, str, float]]) -> pd.DataFrame:
    """(ts, symbol, reason, pnl) -> a TRADES_COLUMNS-shaped ledger."""
    df = pd.DataFrame(rows, columns=["ts", "symbol", "reason", "pnl"])
    df["ts"] = _idx(list(df["ts"]))
    for c in TRADES_COLUMNS:
        if c not in df.columns:
            df[c] = np.nan if c not in ("side", "tag") else (1 if c == "side" else "")
    return df[list(TRADES_COLUMNS)]


def _result(returns: pd.Series, weights: pd.DataFrame | None = None,
            trades: pd.DataFrame | None = None,
            bench: pd.Series | None = None) -> BacktestResult:
    """A BacktestResult without running an engine — keeps the edge cases blunt."""
    idx = returns.index
    w = weights if weights is not None else pd.DataFrame({"MOEX:SBER": 1.0}, index=idx)
    tr = trades if trades is not None else pd.DataFrame(columns=list(TRADES_COLUMNS))
    costs = pd.DataFrame(0.0, index=idx, columns=list(COST_COLUMNS))
    return BacktestResult(
        equity=(1.0 + returns.fillna(0.0)).cumprod(),
        returns_gross=returns, returns_net=returns, weights=w, positions=w.copy(),
        trades=tr, costs=costs, exposure=exposure_frame(w),
        metrics=summary(returns), per_year=per_year_table(returns, returns),
        meta=RunMeta(run_id="t", strategy_key="k", params={"a": 1}, universe="u",
                     start=str(idx[0].date()), end=str(idx[-1].date()), freq="1d",
                     cost_preset="moex_equity", execution_lag=1, overlay=None,
                     created_at="2020-01-01T00:00:00+00:00", engine="weights"),
        benchmark_equity=bench,
    )


# --------------------------------------------------------------------------- #
# monthly                                                                      #
# --------------------------------------------------------------------------- #

def test_monthly_compounds_within_month_and_nulls_empty_months():
    r = pd.Series(
        [0.10, -0.05, np.nan, 0.02, 0.03],
        index=_idx(["2020-01-02", "2020-01-03", "2020-02-04", "2020-03-02", "2021-05-04"]),
    )
    m = monthly_table(r)

    assert m["years"] == [2020, 2021]
    assert m["cells"][0][0] == pytest.approx(1.10 * 0.95 - 1.0)      # compounded, not summed
    assert m["cells"][0][1] is None                                  # all-NaN month -> null
    assert m["cells"][0][2] == pytest.approx(0.02)
    assert [m["cells"][0][i] for i in range(3, 12)] == [None] * 9
    assert m["totals"][0] == pytest.approx(1.10 * 0.95 * 1.02 - 1.0)
    assert m["cells"][1][4] == pytest.approx(0.03)
    assert m["totals"][1] == pytest.approx(0.03)
    json.dumps(m)


def test_monthly_empty_series():
    assert monthly_table(pd.Series(dtype=float)) == {"years": [], "cells": [], "totals": []}


# --------------------------------------------------------------------------- #
# benchmark                                                                    #
# --------------------------------------------------------------------------- #

def test_benchmark_stats_matches_numpy():
    rng = np.random.default_rng(11)
    idx = pd.bdate_range("2018-01-01", periods=400, tz="UTC")
    rb = pd.Series(rng.normal(0.0004, 0.011, len(idx)), index=idx)
    r = pd.Series(0.6 * rb.to_numpy() + rng.normal(0.0002, 0.006, len(idx)), index=idx)
    bench_eq = (1.0 + rb).cumprod()
    bench_eq.name = "MOEX:MCFTR"

    st = benchmark_stats(r, bench_eq)

    # the payload path rebuilds bench returns from the equity, losing bar 0
    b = bench_eq.pct_change().dropna()
    a = r.reindex(b.index).to_numpy()
    b = b.to_numpy()
    beta = np.cov(a, b, ddof=1)[0, 1] / np.var(b, ddof=1)
    d = a - b

    assert st["symbol"] == "MOEX:MCFTR"
    assert st["beta"] == pytest.approx(beta, rel=1e-6)
    assert st["alpha_ann"] == pytest.approx((a.mean() - beta * b.mean()) * 252.0, rel=1e-6)
    assert st["corr"] == pytest.approx(np.corrcoef(a, b)[0, 1], rel=1e-6)
    assert st["te_ann"] == pytest.approx(d.std(ddof=1) * np.sqrt(252.0), rel=1e-6)
    assert st["ir"] == pytest.approx(d.mean() / d.std(ddof=1) * np.sqrt(252.0), rel=1e-6)
    assert st["ann_vol"] == pytest.approx(b.std(ddof=1) * np.sqrt(252.0), rel=1e-6)
    assert st["max_dd"] < 0.0
    json.dumps(st)


def test_benchmark_stats_unnamed_and_absent():
    idx = pd.bdate_range("2020-01-01", periods=30, tz="UTC")
    r = pd.Series(0.001, index=idx)
    assert benchmark_stats(r, None) is None
    assert benchmark_stats(r, pd.Series([1.0], index=idx[:1])) is None
    assert benchmark_stats(r, pd.Series(1.0, index=idx).cumsum())["symbol"] == "benchmark"


# --------------------------------------------------------------------------- #
# trades                                                                       #
# --------------------------------------------------------------------------- #

def test_trade_stats_on_small_ledger():
    tr = _ledger([
        ("2020-01-02", "MOEX:SBER", "entry", np.nan),
        ("2020-01-06", "MOEX:SBER", "take", 0.10),      # 4 days held
        ("2020-01-02", "MOEX:GAZP", "entry", np.nan),
        ("2020-01-04", "MOEX:GAZP", "stop", -0.04),     # 2 days
        ("2020-02-03", "MOEX:SBER", "entry", np.nan),
        ("2020-02-09", "MOEX:SBER", "time", 0.02),      # 6 days
        ("2020-03-02", "MOEX:GAZP", "entry", np.nan),
        ("2020-03-06", "MOEX:GAZP", "stop", -0.01),     # 4 days
    ])
    st = trade_stats(tr)

    assert st["n"] == 4                                  # entry rows are not trades
    assert st["win_rate"] == pytest.approx(0.5)
    assert st["profit_factor"] == pytest.approx(0.12 / 0.05)
    assert st["avg_win"] == pytest.approx(0.06)
    assert st["avg_loss"] == pytest.approx(-0.025)
    assert st["expectancy"] == pytest.approx(0.07 / 4)
    assert st["best"] == pytest.approx(0.10)
    assert st["worst"] == pytest.approx(-0.04)
    assert st["avg_hold_days"] == pytest.approx((4 + 2 + 6 + 4) / 4)
    json.dumps(st)


def test_trade_stats_edge_cases():
    assert trade_stats(None) is None
    assert trade_stats(pd.DataFrame(columns=list(TRADES_COLUMNS))) is None
    # weight-engine ledger: rebalance rows, no realized pnl at all
    assert trade_stats(_ledger([("2020-01-02", "MOEX:SBER", "signal", np.nan)])) is None
    # no losers -> profit_factor null, never inf (JSON.parse rejects Infinity)
    st = trade_stats(_ledger([("2020-01-02", "MOEX:SBER", "take", 0.05)]))
    assert st["profit_factor"] is None and st["avg_loss"] is None
    assert st["avg_hold_days"] is None                   # no entry rows to pair
    json.dumps(st)


# --------------------------------------------------------------------------- #
# drawdowns                                                                    #
# --------------------------------------------------------------------------- #

def test_drawdown_rows_recovered_and_unrecovered():
    idx = pd.bdate_range("2020-01-01", periods=5, tz="UTC")   # 01-01,02,03,06,07
    eq = pd.Series([1.0, 1.2, 0.9, 1.3, 1.1], index=idx)

    rows = drawdown_rows(eq)

    assert len(rows) == 2
    deep, shallow = rows
    assert deep["depth"] == pytest.approx(0.9 / 1.2 - 1.0)
    assert (deep["start"], deep["trough"], deep["end"]) == ("2020-01-02", "2020-01-03", "2020-01-06")
    assert deep["days"] == 2 and deep["recovery_days"] == 1
    # still under water at the last bar -> end/recovery_days null, and its peak
    # is the recovery bar (not the earlier peak)
    assert shallow["depth"] == pytest.approx(1.1 / 1.3 - 1.0)
    assert shallow["start"] == "2020-01-06" and shallow["trough"] == "2020-01-07"
    assert shallow["end"] is None and shallow["recovery_days"] is None
    assert shallow["days"] == 1
    json.dumps(rows)


def test_drawdown_rows_degenerate():
    assert drawdown_rows(pd.Series(dtype=float)) == []
    idx = pd.bdate_range("2020-01-01", periods=5, tz="UTC")
    assert drawdown_rows(pd.Series([1.0, 1.1, 1.2, 1.3, 1.4], index=idx)) == []


# --------------------------------------------------------------------------- #
# rolling                                                                      #
# --------------------------------------------------------------------------- #

def test_rolling_window_length_and_subsampling():
    rng = np.random.default_rng(3)
    idx = pd.bdate_range("2015-01-01", periods=300, tz="UTC")
    r = pd.Series(rng.normal(0.0005, 0.01, len(idx)), index=idx)

    roll = rolling_stats(r)
    assert len(roll["ts"]) == 300 - 251                  # warm-up skipped, not padded
    assert len(roll["sharpe"]) == len(roll["vol"]) == len(roll["ts"])
    assert roll["beta"] is None                          # whole key null without a benchmark
    last = r.iloc[-252:]
    assert roll["vol"][-1] == pytest.approx(last.std(ddof=1) * np.sqrt(252.0))
    assert roll["sharpe"][-1] == pytest.approx(
        last.mean() / last.std(ddof=1) * np.sqrt(252.0))
    assert roll["ts"][-1] == int(idx[-1].timestamp())
    json.dumps(roll)


def test_rolling_short_series_is_empty_not_a_crash():
    idx = pd.bdate_range("2020-01-01", periods=100, tz="UTC")
    r = pd.Series(0.001, index=idx)
    assert rolling_stats(r) == {"ts": [], "sharpe": [], "vol": [], "beta": None}
    assert rolling_stats(r, r)["beta"] == []             # bench given -> [] not None


def test_rolling_downsamples_to_1500_points_with_beta():
    rng = np.random.default_rng(5)
    idx = pd.bdate_range("1995-01-02", periods=5000, tz="UTC")
    r = pd.Series(rng.normal(0.0005, 0.01, len(idx)), index=idx)
    rb = pd.Series(rng.normal(0.0004, 0.009, len(idx)), index=idx)

    roll = rolling_stats(r, rb)
    assert len(roll["ts"]) == 1500
    assert len(roll["sharpe"]) == len(roll["vol"]) == len(roll["beta"]) == 1500
    assert all(v is not None for v in roll["beta"])
    w_r, w_b = r.iloc[-252:], rb.iloc[-252:]
    assert roll["beta"][-1] == pytest.approx(
        np.cov(w_r, w_b, ddof=1)[0, 1] / np.var(w_b, ddof=1), rel=1e-9)


# --------------------------------------------------------------------------- #
# attribution                                                                  #
# --------------------------------------------------------------------------- #

def test_attribution_exact_paths_and_capital_share_proxy():
    idx = pd.bdate_range("2020-01-01", periods=4, tz="UTC")
    w = pd.DataFrame({"A": [0.5, 0.5, 0.5, 0.5], "B": [-0.25, -0.25, 0.0, 0.0]}, index=idx)

    # 1) per-symbol returns available -> exact sum(w * r)
    rets = pd.DataFrame({"A": [0.01] * 4, "B": [0.02] * 4}, index=idx)
    exact = {row["symbol"]: row for row in attribution_rows(w, rets)}
    assert exact["A"]["pnl"] == pytest.approx(4 * 0.5 * 0.01)
    assert exact["B"]["pnl"] == pytest.approx(2 * -0.25 * 0.02)
    assert exact["A"]["avg_weight"] == pytest.approx(0.5)
    assert exact["B"]["avg_weight"] == pytest.approx(0.125)      # mean |w|

    # 2) realized pnl in the ledger wins over the proxy
    tr = _ledger([("2020-01-02", "A", "take", 0.03), ("2020-01-02", "B", "stop", -0.01),
                  ("2020-01-01", "A", "entry", np.nan)])
    rows = attribution_rows(w, pd.Series(0.001, index=idx), tr)
    assert [row["symbol"] for row in rows] == ["A", "B"]         # sorted by pnl desc
    assert rows[0]["pnl"] == pytest.approx(0.03) and rows[0]["n_trades"] == 2
    assert rows[1]["pnl"] == pytest.approx(-0.01) and rows[1]["n_trades"] == 1

    # 3) proxy: the day's portfolio return split by share of gross exposure
    proxy = {row["symbol"]: row for row in attribution_rows(w, pd.Series(0.001, index=idx))}
    assert proxy["A"]["pnl"] == pytest.approx(0.001 * (2 / 3) * 2 + 0.001 * 2)
    assert proxy["B"]["pnl"] == pytest.approx(0.001 * (1 / 3) * 2)
    assert sum(row["pnl"] for row in proxy.values()) == pytest.approx(4 * 0.001)


def test_attribution_empty_inputs():
    assert attribution_rows(None, None, None) == []
    assert attribution_rows(pd.DataFrame(), None, pd.DataFrame(columns=list(TRADES_COLUMNS))) == []


# --------------------------------------------------------------------------- #
# payload                                                                      #
# --------------------------------------------------------------------------- #

def test_to_run_json_v2_is_complete_and_serializable():
    """Full smoke test on a real engine run: every v2 key present, json.dumps
    clean (no numpy scalars, no NaN/Infinity tokens)."""
    from qbt.engine.cost_models import FlatCostModel
    from qbt.engine.costs import CostParams
    from qbt.engine.runner import run_backtest
    from qbt.strategy.base import Strategy
    from qbt.testing.synthetic import make_context

    class _BuyHold(Strategy):
        key = "_test_report_bh"
        name = "bh"
        doc_path = ""
        output = "weights"

        def generate(self, ctx):
            return pd.DataFrame(1.0 / len(ctx.symbols), index=ctx.calendar, columns=ctx.symbols)

    ctx = make_context(3, "2018-01-01", "2021-12-31", seed=4)
    res = run_backtest(_BuyHold(), ctx,
                       cost_model=FlatCostModel(CostParams(commission_bps=2)))
    out = res.to_run_json()

    for k in V1_KEYS + V2_KEYS:
        assert k in out, k
    blob = json.dumps(out)                     # must not raise; must not emit NaN/Infinity
    assert "NaN" not in blob and "Infinity" not in blob
    assert json.loads(blob)["n_trades"] == out["n_trades"]

    assert "n_positions" in out["exposure"]    # v2 adds it to the existing dict
    assert len(out["exposure"]["n_positions"]) == len(out["exposure"]["gross"])
    assert out["benchmark_stats"]["symbol"]
    assert out["monthly"]["years"][0] == 2018
    assert len(out["monthly"]["cells"]) == len(out["monthly"]["totals"])
    assert len(out["rolling"]["ts"]) == len(out["rolling"]["sharpe"]) > 0
    assert len(out["rolling"]["beta"]) == len(out["rolling"]["ts"])
    assert {"symbol", "pnl", "avg_weight", "n_trades"} == set(out["attribution"][0])
    assert len(out["attribution"]) <= 50
    assert all(set(d) == {"start", "trough", "end", "depth", "days", "recovery_days"}
               for d in out["drawdowns"])


def test_to_run_json_degenerate_run_keeps_every_key():
    """No benchmark, empty ledger, 10 bars: keys present, nothing raises."""
    idx = pd.bdate_range("2020-01-01", periods=10, tz="UTC")
    res = _result(pd.Series(np.linspace(-0.01, 0.01, 10), index=idx))
    out = res.to_run_json()

    for k in V1_KEYS + V2_KEYS:
        assert k in out, k
    assert out["benchmark_stats"] is None
    assert out["trade_stats"] is None
    assert out["rolling"] == {"ts": [], "sharpe": [], "vol": [], "beta": None}
    assert out["monthly"]["years"] == [2020]
    json.dumps(out)


def test_to_run_json_order_engine_ledger_fills_trade_stats():
    idx = pd.bdate_range("2020-01-01", periods=40, tz="UTC")
    tr = _ledger([("2020-01-01", "MOEX:SBER", "entry", np.nan),
                  ("2020-01-08", "MOEX:SBER", "take", 0.04),
                  ("2020-01-09", "MOEX:GAZP", "entry", np.nan),
                  ("2020-01-13", "MOEX:GAZP", "stop", -0.02)])
    w = pd.DataFrame({"MOEX:SBER": 0.5, "MOEX:GAZP": 0.25}, index=idx)
    res = _result(pd.Series(0.001, index=idx), weights=w, trades=tr,
                  bench=pd.Series(np.linspace(1.0, 1.1, 40), index=idx, name="MOEX:MCFTR"))
    out = res.to_run_json()

    assert out["trade_stats"]["n"] == 2
    assert out["trade_stats"]["avg_hold_days"] == pytest.approx((7 + 4) / 2)
    assert out["benchmark_stats"]["symbol"] == "MOEX:MCFTR"
    assert [row["symbol"] for row in out["attribution"]] == ["MOEX:SBER", "MOEX:GAZP"]
    assert out["attribution"][0]["pnl"] == pytest.approx(0.04)
    json.dumps(out)


# --------------------------------------------------------------------------- #
# sweep IS/OOS                                                                 #
# --------------------------------------------------------------------------- #

def test_is_oos_sharpe_splits_at_70_percent():
    from qbt.analytics.metrics import sharpe

    rng = np.random.default_rng(9)
    idx = pd.bdate_range("2020-01-01", periods=100, tz="UTC")
    r = pd.Series(rng.normal(0.001, 0.01, len(idx)), index=idx)

    is_, oos = is_oos_sharpe(r)
    assert is_ == pytest.approx(sharpe(r.iloc[:70]))
    assert oos == pytest.approx(sharpe(r.iloc[70:]))
    assert is_oos_sharpe(pd.Series(dtype=float)) == (None, None)
    assert is_oos_sharpe(pd.Series([0.01, 0.02, 0.03], index=idx[:3])) == (None, None)
    # a flat side has zero vol -> nan sharpe -> null, not a crash
    flat = pd.Series([0.0] * 70 + list(rng.normal(0.001, 0.01, 30)), index=idx)
    assert is_oos_sharpe(flat)[0] is None
