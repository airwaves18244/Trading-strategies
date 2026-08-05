"""Read-time price adjustment (WS-A).

The store keeps RAW prices only (per BarStore contract); split-adjusted and
total-return series are derived here at read time.

Backward-looking safety: both `split_adjust` and `build_total_return` are
pure functions of the (close, actions) they're given. A dividend with
``ex_date = d`` only ever contributes to the output series from row ``d``
onward — earlier rows are untouched by it. Concretely: if you slice the raw
close/actions inputs to some cutoff ``t`` and recompute, you get exactly the
same values (up to `t`) as slicing the full recomputed series at `t`. This is
what makes it safe to sit behind `DataContext.slice(t)` in the lookahead
harness.
"""
from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd

from qbt.core.types import CorporateAction, to_utc


def split_adjust(prices: pd.DataFrame, actions: Sequence[CorporateAction]) -> pd.DataFrame:
    """Back-adjust a wide price frame (index=ts, columns=symbol) for stock splits.

    `CorporateAction.value` for kind="split" is the split ratio (e.g. 2.0 for
    a 2-for-1 split: 1 old share -> 2 new shares, price roughly halves).
    Historical prices strictly before a split's ex_date are divided by the
    ratio so the whole series is expressed in current-share terms. Multiple
    splits on the same symbol compound correctly regardless of input order.
    """
    out = prices.copy()
    by_symbol: dict[str, list[CorporateAction]] = {}
    for a in actions:
        if a.kind == "split":
            by_symbol.setdefault(a.symbol, []).append(a)

    for symbol, acts in by_symbol.items():
        if symbol not in out.columns:
            continue
        factor = pd.Series(1.0, index=out.index)
        for a in sorted(acts, key=lambda x: x.ex_date):
            ex_ts = to_utc(a.ex_date)
            before = out.index < ex_ts
            factor = factor.where(~before, factor / a.value)
        out[symbol] = out[symbol] * factor
    return out


def build_total_return(close: pd.DataFrame, actions: Sequence[CorporateAction]) -> pd.DataFrame:
    """Total-return index: split-adjusted close with dividends reinvested on ex-date.

    ``factor_t = (adj_close_t + div_t) / adj_close_{t-1}`` where ``div_t`` is
    any dividend whose ex_date falls on (or, if ex_date isn't a trading day,
    the next trading day on/after) row ``t`` — i.e. exactly the
    ``1 + div / close_prev_ex`` rule, expressed multiplicatively. The index is
    built via cumulative log-factors (numerically stable over long histories)
    and anchored to equal the split-adjusted close on each symbol's first
    valid date.
    """
    adj_close = split_adjust(close, actions)
    idx = adj_close.index
    columns = adj_close.columns

    div_amt = pd.DataFrame(0.0, index=idx, columns=columns)
    col_pos = {c: i for i, c in enumerate(columns)}
    for a in actions:
        if a.kind != "div" or a.symbol not in col_pos:
            continue
        ex_ts = to_utc(a.ex_date)
        pos = idx.searchsorted(ex_ts, side="left")
        if pos >= len(idx):
            continue  # dividend ex-dated after the requested window: nothing to do (yet)
        div_amt.iloc[pos, col_pos[a.symbol]] += a.value

    prev_close = adj_close.shift(1)
    factor = (adj_close + div_amt) / prev_close
    valid = prev_close.notna() & (prev_close != 0) & adj_close.notna()
    with np.errstate(divide="ignore", invalid="ignore"):
        log_factor = np.log(factor.where(valid))
    cum = log_factor.fillna(0.0).cumsum()

    tr = pd.DataFrame(index=idx, columns=columns, dtype=float)
    for symbol in columns:
        s = adj_close[symbol]
        first_valid = s.first_valid_index()
        if first_valid is None:
            continue
        base = s.loc[first_valid]
        cs = cum[symbol]
        tr[symbol] = base * np.exp(cs - cs.loc[first_valid])
        tr.loc[tr.index < first_valid, symbol] = np.nan
    return tr


__all__ = ["split_adjust", "build_total_return"]
