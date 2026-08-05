"""Event-study family engine (WS-D1): event table -> overlapping-cohort weights.

Used by PEAD, index rebalancing, buybacks/insider, lockups, macro drift, merger arb.
Events arrive via ctx.events["<schema>"] (validated by qbt.data.schemas).
"""
from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd

_DATE_CANDIDATES = ("announce_date", "event_date", "report_ts", "release_ts",
                    "effective_date", "lockup_expiry", "ex_date", "ts", "date")


def event_dates(events: pd.DataFrame, date_col: str | None = None) -> pd.Series:
    """Extract the event timestamp column (UTC) — explicit or first known name."""
    col = date_col or next((c for c in _DATE_CANDIDATES if c in events.columns), None)
    if col is None:
        raise ValueError(f"No recognizable date column in events; have {list(events.columns)}")
    return pd.to_datetime(events[col], utc=True)


def event_weights(
    events: pd.DataFrame,
    calendar: pd.DatetimeIndex,
    symbols: Sequence[str],
    entry_lag_bars: int = 2,
    holding_bars: int = 60,
    side: int | str = 1,
    weight_per_event: float = 0.02,
    max_gross: float = 1.0,
    symbol_col: str = "symbol",
    date_col: str | None = None,
) -> pd.DataFrame:
    """Overlapping-cohort event portfolio.

    Per event: position of `weight_per_event * side` in the event's symbol from
    calendar bar (event_bar + entry_lag_bars) for `holding_bars` bars. Cohorts
    accumulate; total gross is capped at `max_gross` by proportional scaling.
    `side` may be a column name holding +1/-1 per event.
    """
    w = pd.DataFrame(0.0, index=calendar, columns=list(symbols))
    if events is None or not len(events):
        return w
    ts = event_dates(events, date_col)
    sides = events[side] if isinstance(side, str) else pd.Series(side, index=events.index)
    for i in events.index:
        sym = events.at[i, symbol_col] if symbol_col in events.columns else None
        if sym is None or sym not in w.columns:
            continue
        pos = calendar.searchsorted(ts.loc[i], side="right") - 1 + entry_lag_bars
        if pos >= len(calendar) or pos < 0:
            continue
        end = min(pos + holding_bars, len(calendar))
        w.iloc[pos:end, w.columns.get_loc(sym)] += float(sides.loc[i]) * weight_per_event
    gross = w.abs().sum(axis=1)
    scale = np.where(gross > max_gross, max_gross / gross.replace(0, np.nan), 1.0)
    return w.mul(pd.Series(scale, index=w.index).fillna(1.0), axis=0)


def car_table(
    events: pd.DataFrame,
    total_return: pd.DataFrame,
    window: tuple[int, int] = (-5, 60),
    symbol_col: str = "symbol",
    date_col: str | None = None,
) -> pd.DataFrame:
    """Cumulative abnormal return curve (vs equal-weight universe mean) in event time.

    Returns DataFrame indexed by event-relative bar with columns [mean_car, n].
    """
    r = total_return.pct_change(fill_method=None)
    bench = r.mean(axis=1)
    ts = event_dates(events, date_col)
    lo, hi = window
    grid = range(lo, hi + 1)
    acc = {k: [] for k in grid}
    cal = total_return.index
    for i in events.index:
        sym = events.at[i, symbol_col] if symbol_col in events.columns else None
        if sym not in r.columns:
            continue
        pos = cal.searchsorted(ts.loc[i], side="right") - 1
        car = 0.0
        for k in grid:
            j = pos + k
            if 0 <= j < len(cal):
                ar = (r.iat[j, r.columns.get_loc(sym)] or 0.0) - (bench.iat[j] or 0.0)
                if np.isfinite(ar):
                    car += ar
                acc[k].append(car)
    rows = [{"event_bar": k, "mean_car": float(np.mean(v)) if v else np.nan, "n": len(v)}
            for k, v in acc.items()]
    return pd.DataFrame(rows).set_index("event_bar")
