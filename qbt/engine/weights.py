"""WeightEngine — vectorized portfolio backtest over a target-weights matrix (WS-C).

Convention: after shift_for_execution(lag), row t of the executed weights is the
position HELD during bar t, so pnl_t = w_exec[t] · r[t]. Costs are charged on
weight changes, sized against the pre-cost (gross) equity path to stay vectorized.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from qbt.core.types import PriceKind
from qbt.engine.context import DataContext
from qbt.engine.costs import CostModel
from qbt.engine.portfolio import exposure_frame, trades_from_weight_changes, turnover_series
from qbt.engine.result import COST_COLUMNS, BacktestResult, RunMeta
from qbt.engine.risk import shift_for_execution


class WeightEngine:
    name = "weights"

    def run(
        self,
        weights: pd.DataFrame,
        ctx: DataContext,
        cost_model: CostModel,
        lag: int = 1,
        initial_nav: float = 1.0,
        meta: RunMeta | None = None,
    ) -> BacktestResult:
        cal = ctx.calendar
        w = weights.reindex(index=cal, columns=ctx.symbols).astype(float)
        # universe hygiene: no weight on non-members; forced flat when a name leaves
        w = w.where(ctx.universe_mask.reindex_like(w).fillna(False), 0.0).fillna(0.0)

        w_exec = shift_for_execution(w, lag=lag)

        r = ctx.ret(PriceKind.TOTAL_RETURN).reindex_like(w_exec)
        if ctx.delisting_return is not None:
            dl = ctx.delisting_return.reindex_like(r)
            r = r.where(dl.isna(), dl)
        r = r.fillna(0.0)

        gross = (w_exec * r).sum(axis=1)
        equity_gross = (1.0 + gross).cumprod() * 1.0

        # traded notional against lagged gross equity (pre-cost proxy, documented)
        dw = w_exec.diff()
        if len(dw):
            dw.iloc[0] = w_exec.iloc[0]
        nav_prev = (equity_gross.shift(1).fillna(1.0)) * initial_nav
        traded_notional = dw.abs().mul(nav_prev, axis=0)

        adv = ctx.adv(20) * np.nan if ctx.value is None else ctx.adv(20)
        spread_override = ctx.extras.get("spread_bps")
        cost_bps = cost_model.trade_cost_bps(traded_notional, adv, spread_override)
        trade_cost_frac = (dw.abs() * cost_bps.reindex_like(dw).fillna(0.0) / 1e4).sum(axis=1)

        pos_notional = w_exec.mul(nav_prev, axis=0)
        hold_bps = cost_model.holding_cost_bps(pos_notional)
        hold_cost_frac = (w_exec.abs() * hold_bps.reindex_like(w_exec).fillna(0.0) / 1e4).sum(axis=1)

        net = gross - trade_cost_frac - hold_cost_frac
        equity = (1.0 + net).cumprod() * initial_nav

        # cost breakdown (fractions of NAV per day)
        comp = getattr(cost_model, "trade_cost_components", None)
        costs = pd.DataFrame(0.0, index=cal, columns=list(COST_COLUMNS))
        if callable(comp):
            parts = comp(traded_notional, adv, spread_override)
            for key in ("commission", "spread", "impact"):
                if key in parts:
                    costs[key] = (dw.abs() * parts[key].reindex_like(dw).fillna(0.0) / 1e4).sum(axis=1)
        else:
            costs["commission"] = trade_cost_frac
        costs["borrow"] = hold_cost_frac

        nav_series = equity
        trades = trades_from_weight_changes(w_exec, ctx.close, nav_series, cost_bps)

        from qbt.analytics.metrics import per_year_table, summary
        metrics = summary(net, returns_gross=gross, positions=w_exec, trades=trades,
                          ppy=ctx.ann_factor)
        metrics["turnover_ann"] = float(turnover_series(w_exec).mean() * ctx.ann_factor)
        per_year = per_year_table(gross, net, costs, trades=trades)

        bench = None
        if ctx.benchmark is not None and len(ctx.benchmark.dropna()):
            b = ctx.benchmark.reindex(cal).ffill()
            bench = (b / b.dropna().iloc[0]) * initial_nav

        return BacktestResult(
            equity=equity, returns_gross=gross, returns_net=net,
            weights=w_exec, positions=w_exec.copy(), trades=trades, costs=costs,
            exposure=exposure_frame(w_exec), metrics=metrics, per_year=per_year,
            meta=meta or RunMeta(run_id="", strategy_key="", params={}, universe="",
                                 start=str(cal[0].date()) if len(cal) else "",
                                 end=str(cal[-1].date()) if len(cal) else "",
                                 freq=str(ctx.freq), cost_preset="", execution_lag=lag,
                                 overlay=None, created_at="", engine="weights"),
            benchmark_equity=bench,
        )
