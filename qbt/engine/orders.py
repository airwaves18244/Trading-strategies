"""OrderEngine — bar-loop backtest for OrderIntent strategies (WS-C).

Fill rules (conservative, per docs/architecture.md):
  - entries execute at the next bar OPEN after intent.ts;
  - stop & take both touched within one bar => STOP fills first;
  - gap through a level => fill at the open (worse than the level);
  - time_stop_bars exits at that bar's close;
  - sizing resolved against runtime NAV per OrderIntent.size_mode.

Normalization: `weights` in the result = realized position notional / NAV.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from qbt.engine.context import DataContext
from qbt.engine.costs import CostModel
from qbt.engine.portfolio import exposure_frame
from qbt.engine.result import COST_COLUMNS, TRADES_COLUMNS, BacktestResult, RunMeta
from qbt.strategy.base import OrderIntent


class _Position:
    __slots__ = ("symbol", "side", "qty", "entry_px", "stop", "take", "bars_held",
                 "time_stop", "tag", "entry_ts")

    def __init__(self, symbol, side, qty, entry_px, stop, take, time_stop, tag, entry_ts):
        self.symbol, self.side, self.qty = symbol, side, qty
        self.entry_px, self.stop, self.take = entry_px, stop, take
        self.time_stop, self.tag, self.entry_ts = time_stop, tag, entry_ts
        self.bars_held = 0


class OrderEngine:
    name = "orders"

    def __init__(self, cost_bps_flat: float | None = None):
        self._flat_bps = cost_bps_flat

    def run(
        self,
        intents: list[OrderIntent],
        ctx: DataContext,
        cost_model: CostModel,
        initial_nav: float = 1.0,
        meta: RunMeta | None = None,
    ) -> BacktestResult:
        cal = ctx.calendar
        n = len(cal)
        idx_of = {ts: i for i, ts in enumerate(cal)}
        opens, highs, lows, closes = ctx.open, ctx.high, ctx.low, ctx.close

        # queue entries by execution bar index
        pending: dict[int, list[OrderIntent]] = {}
        for it in sorted(intents, key=lambda x: x.ts):
            ts = pd.Timestamp(it.ts)
            if ts.tzinfo is None:
                ts = ts.tz_localize("UTC")
            pos_arr = cal.searchsorted(ts, side="right")  # next bar strictly after intent.ts
            if pos_arr < n:
                pending.setdefault(int(pos_arr), []).append(it)

        cash = initial_nav
        positions: dict[str, _Position] = {}
        nav_hist = np.full(n, np.nan)
        trades: list[dict] = []
        weights_rows = np.zeros((n, len(ctx.symbols)))
        sym_idx = {s: j for j, s in enumerate(ctx.symbols)}
        base_trade_bps = (
            self._flat_bps if self._flat_bps is not None
            else cost_model.params.commission_bps + cost_model.params.exchange_fee_bps
            + cost_model.params.half_spread_bps
        )

        def px(frame: pd.DataFrame, i: int, sym: str) -> float:
            v = frame.iat[i, frame.columns.get_loc(sym)]
            return float(v) if pd.notna(v) else np.nan

        def mark_nav(i: int) -> float:
            total = cash
            for p in positions.values():
                c = px(closes, i, p.symbol)
                if np.isfinite(c):
                    total += p.side * p.qty * c
            return total

        def record_trade(ts, p: _Position, price: float, reason: str, qty: float | None = None):
            q = qty if qty is not None else p.qty
            notional = q * price
            cost = notional * base_trade_bps / 1e4
            pnl = p.side * q * (price - p.entry_px) - cost if reason != "entry" else np.nan
            trades.append({
                "ts": ts, "symbol": p.symbol, "side": p.side if reason == "entry" else -p.side,
                "qty": q, "price": price, "notional": notional,
                "cost_bps": base_trade_bps, "reason": reason, "tag": p.tag, "pnl": pnl,
            })
            return cost

        for i in range(n):
            ts = cal[i]
            nav_open = mark_nav(i - 1) if i > 0 else cash

            # 1) exits on this bar (stops/takes/time) using OHLC
            for sym in list(positions):
                p = positions[sym]
                o, h, lo, c = px(opens, i, sym), px(highs, i, sym), px(lows, i, sym), px(closes, i, sym)
                if not np.isfinite(c):
                    continue
                exit_px, reason = None, None
                if p.side > 0:
                    if p.stop is not None and np.isfinite(o) and o <= p.stop:
                        exit_px, reason = o, "stop"          # gap through stop
                    elif p.stop is not None and np.isfinite(lo) and lo <= p.stop:
                        exit_px, reason = p.stop, "stop"     # stop before take (conservative)
                    elif p.take is not None and np.isfinite(o) and o >= p.take:
                        exit_px, reason = o, "take"
                    elif p.take is not None and np.isfinite(h) and h >= p.take:
                        exit_px, reason = p.take, "take"
                else:
                    if p.stop is not None and np.isfinite(o) and o >= p.stop:
                        exit_px, reason = o, "stop"
                    elif p.stop is not None and np.isfinite(h) and h >= p.stop:
                        exit_px, reason = p.stop, "stop"
                    elif p.take is not None and np.isfinite(o) and o <= p.take:
                        exit_px, reason = o, "take"
                    elif p.take is not None and np.isfinite(lo) and lo <= p.take:
                        exit_px, reason = p.take, "take"
                p.bars_held += 1
                if exit_px is None and p.time_stop is not None and p.bars_held >= p.time_stop:
                    exit_px, reason = c, "time"
                if exit_px is not None:
                    cost = record_trade(ts, p, exit_px, reason)
                    cash += p.side * p.qty * exit_px - cost
                    del positions[sym]

            # 2) entries queued for this bar at open
            for it in pending.get(i, ()):
                o = px(opens, i, it.symbol)
                if not np.isfinite(o) or it.symbol in positions:
                    continue
                nav_now = mark_nav(i - 1) if i > 0 else cash
                if it.size_mode == "risk_frac":
                    if it.stop is None:
                        raise ValueError(f"risk_frac intent for {it.symbol} requires a stop")
                    per_unit_risk = abs(o - it.stop)
                    if per_unit_risk <= 0:
                        continue
                    qty = nav_now * it.size / per_unit_risk
                elif it.size_mode == "nav_frac":
                    qty = nav_now * it.size / o
                elif it.size_mode == "target_weight":
                    qty = nav_now * abs(it.size) / o
                elif it.size_mode == "qty":
                    qty = it.size
                else:
                    raise ValueError(f"unknown size_mode {it.size_mode}")
                if qty <= 0:
                    continue
                p = _Position(it.symbol, it.side, qty, o, it.stop, it.take,
                              it.time_stop_bars, it.tag, ts)
                cost = record_trade(ts, p, o, "entry")
                cash -= it.side * qty * o + cost
                positions[it.symbol] = p

            # 3) forced close for names leaving the universe
            for sym in list(positions):
                if sym in ctx.universe_mask.columns and not bool(ctx.universe_mask.iat[i, ctx.universe_mask.columns.get_loc(sym)]):
                    p = positions[sym]
                    c = px(closes, i, sym)
                    if np.isfinite(c):
                        cost = record_trade(ts, p, c, "delist")
                        cash += p.side * p.qty * c - cost
                        del positions[sym]

            nav = mark_nav(i)
            nav_hist[i] = nav
            for sym, p in positions.items():
                c = px(closes, i, sym)
                if np.isfinite(c) and nav > 0:
                    weights_rows[i, sym_idx[sym]] = p.side * p.qty * c / nav

        equity = pd.Series(nav_hist, index=cal).ffill().fillna(initial_nav)
        net = equity.pct_change().fillna(0.0)
        gross = net  # per-trade costs already embedded; gross≈net + cost add-back below
        trades_df = pd.DataFrame(trades, columns=list(TRADES_COLUMNS))
        cost_frac = pd.Series(0.0, index=cal)
        if len(trades_df):
            per_day = trades_df.assign(cost=lambda d: d.notional * d.cost_bps / 1e4).groupby("ts")["cost"].sum()
            cost_frac = per_day.reindex(cal).fillna(0.0) / equity.shift(1).fillna(initial_nav)
            gross = net + cost_frac

        weights = pd.DataFrame(weights_rows, index=cal, columns=ctx.symbols)
        costs = pd.DataFrame(0.0, index=cal, columns=list(COST_COLUMNS))
        costs["commission"] = cost_frac

        from qbt.analytics.metrics import per_year_table, summary
        metrics = summary(net, returns_gross=gross, positions=weights, trades=trades_df,
                          ppy=ctx.ann_factor)
        per_year = per_year_table(gross, net, costs, trades=trades_df)

        bench = None
        if ctx.benchmark is not None and len(ctx.benchmark.dropna()):
            b = ctx.benchmark.reindex(cal).ffill()
            bench = (b / b.dropna().iloc[0]) * initial_nav

        return BacktestResult(
            equity=equity, returns_gross=gross, returns_net=net, weights=weights,
            positions=weights.copy(), trades=trades_df, costs=costs,
            exposure=exposure_frame(weights), metrics=metrics, per_year=per_year,
            meta=meta or RunMeta(run_id="", strategy_key="", params={}, universe="",
                                 start=str(cal[0].date()) if n else "",
                                 end=str(cal[-1].date()) if n else "",
                                 freq=str(ctx.freq), cost_preset="", execution_lag=1,
                                 overlay=None, created_at="", engine="orders"),
            benchmark_equity=bench,
        )
