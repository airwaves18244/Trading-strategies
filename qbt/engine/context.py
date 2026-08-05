"""DataContext — the ONLY data door for strategies. PHASE 0 CONTRACT (fully implemented).

Strategies receive a DataContext and nothing else; the look-ahead harness relies on
slice(end) producing a context whose every field stops at `end`.

All frames: index = calendar (UTC tz-aware DatetimeIndex), columns = canonical symbols.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace

import numpy as np
import pandas as pd

from qbt.core.types import Freq, Instrument, PriceKind, annualization_factor


@dataclass
class DataContext:
    calendar: pd.DatetimeIndex
    instruments: Mapping[str, Instrument]
    open: pd.DataFrame
    high: pd.DataFrame
    low: pd.DataFrame
    close: pd.DataFrame
    total_return: pd.DataFrame          # TR index (dividends reinvested), same shape
    volume: pd.DataFrame
    value: pd.DataFrame                 # turnover in currency (ADV source)
    universe_mask: pd.DataFrame         # bool: PIT member AND tradable AND not halted
    delisting_return: pd.DataFrame | None = None   # sparse; applied on last trading day
    freq: Freq = Freq.D1
    #: named event tables (validated against qbt.data.schemas), e.g. {"deals": df}
    events: dict[str, pd.DataFrame] = field(default_factory=dict)
    #: auxiliary frames keyed by name (e.g. "basis", "funding", "vol_curve_slope")
    extras: dict[str, pd.DataFrame] = field(default_factory=dict)
    #: benchmark close series (e.g. IMOEX) for reporting
    benchmark: pd.Series | None = None

    # ---------------- derived helpers ----------------

    def ret(self, kind: PriceKind = PriceKind.TOTAL_RETURN) -> pd.DataFrame:
        """Simple returns from close or total-return series."""
        px = self.total_return if kind == PriceKind.TOTAL_RETURN else self.close
        return px.pct_change(fill_method=None)

    def adv(self, window: int = 20) -> pd.DataFrame:
        """Average daily value (currency turnover), strictly trailing."""
        return self.value.rolling(window, min_periods=max(3, window // 3)).mean().shift(1)

    def rebalance_dates(self, freq: str = "ME") -> pd.DatetimeIndex:
        """Calendar subset for rebalancing. freq: 'D', 'W' (last trading day of week),
        'ME' (last trading day of month), 'QE' (quarter)."""
        if freq == "D":
            return self.calendar
        naive = self.calendar.tz_convert("UTC").tz_localize(None)
        periods = {"W": naive.to_period("W"), "ME": naive.to_period("M"),
                   "QE": naive.to_period("Q")}[freq]
        last = pd.Series(self.calendar, index=periods).groupby(level=0).max()
        out = pd.DatetimeIndex(last.values, tz="UTC")
        # Drop the trailing INCOMPLETE period: if more business days of the last
        # period exist beyond the calendar end (data cut mid-period), its "last
        # trading day" isn't known yet. Keeps slice(t) consistent with the full
        # run — the look-ahead harness depends on this.
        if len(out):
            end_naive = naive[-1]
            nxt = end_naive + pd.offsets.BDay(1)
            same_period = {"W": nxt.to_period("W") == periods[-1],
                           "ME": nxt.to_period("M") == periods[-1],
                           "QE": nxt.to_period("Q") == periods[-1]}[freq]
            if same_period:
                out = out[:-1]
        return out

    def slice(self, end: pd.Timestamp) -> "DataContext":
        """Context truncated to <= end. THE mechanism behind assert_no_lookahead."""
        end = pd.Timestamp(end)
        if end.tzinfo is None:
            end = end.tz_localize("UTC")
        cal = self.calendar[self.calendar <= end]

        def cut(df: pd.DataFrame | None) -> pd.DataFrame | None:
            return None if df is None else df.loc[df.index <= end]

        ev = {}
        for name, df in self.events.items():
            tcol = next((c for c in ("announce_date", "event_date", "report_ts", "release_ts",
                                     "asof_date", "ts", "date") if c in df.columns), None)
            ev[name] = df if tcol is None else df[pd.to_datetime(df[tcol], utc=True) <= end]
        return replace(
            self, calendar=cal,
            open=cut(self.open), high=cut(self.high), low=cut(self.low),
            close=cut(self.close), total_return=cut(self.total_return),
            volume=cut(self.volume), value=cut(self.value),
            universe_mask=cut(self.universe_mask),
            delisting_return=cut(self.delisting_return),
            events=ev,
            extras={k: cut(v) for k, v in self.extras.items()},
            benchmark=None if self.benchmark is None else self.benchmark.loc[self.benchmark.index <= end],
        )

    @property
    def ann_factor(self) -> float:
        return annualization_factor(self.freq)

    @property
    def symbols(self) -> list[str]:
        return list(self.close.columns)
