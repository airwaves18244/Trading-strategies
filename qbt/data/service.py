"""DataService (WS-A): fetch-only-gaps ingestion + DataContext assembly.

`ensure()` is the incremental-fetch entry point (backs `qbt data ensure`):
for each symbol it diffs the requested [start, end] against the trading
calendar and what's already in the store (`BarStore.missing_ranges`), fetches
only the gaps (chunked to respect provider capabilities), validates, writes,
and updates the manifest.

`load_context()` assembles a `DataContext` purely from what's already in the
store (no network) — wide frames, a total-return series via
`qbt.data.adjust`, an optional universe mask, and an optional benchmark
series. Assembly is intentionally minimal: it does not try to be clever
about missing data, backfilling, or interpolation.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from datetime import datetime

import numpy as np
import pandas as pd

from qbt.core.errors import ProviderError
from qbt.core.types import (
    BarFrame, BarRequest, CorporateAction, Freq, Instrument, PriceKind, to_utc,
)
from qbt.data.adjust import build_total_return
from qbt.data.interfaces import BarStore, MarketDataProvider, Universe
from qbt.data.manifest import Manifest
from qbt.engine.context import DataContext

ProgressCb = Callable[[int, int], None]
CalendarFn = Callable[[datetime, datetime], pd.DatetimeIndex]

_DEFAULT_CHUNK_DAYS = 365


def _chunk_range(
    start: pd.Timestamp, end: pd.Timestamp, chunk_days: int, max_history_days: int | None
) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    limit = chunk_days if max_history_days is None else min(chunk_days, max_history_days)
    limit = max(limit, 1)
    step = pd.Timedelta(days=limit)
    out: list[tuple[pd.Timestamp, pd.Timestamp]] = []
    cur = start
    while cur <= end:
        nxt = min(cur + step, end)
        out.append((cur, nxt))
        cur = nxt + pd.Timedelta(days=1)
    return out


def _build_delisting_frame(
    instruments: Mapping[str, Instrument],
    calendar: pd.DatetimeIndex,
    symbols: Sequence[str],
    pct: float,
) -> pd.DataFrame | None:
    any_set = False
    df = pd.DataFrame(np.nan, index=calendar, columns=list(symbols))
    for symbol in symbols:
        inst = instruments.get(symbol)
        if inst is None or inst.listed_to is None:
            continue
        d = to_utc(inst.listed_to)
        prior = calendar[calendar <= d]
        if len(prior) == 0:
            continue
        df.at[prior[-1], symbol] = pct
        any_set = True
    return df if any_set else None


class DataService:
    def __init__(
        self,
        store: BarStore,
        manifest: Manifest,
        providers: dict[str, MarketDataProvider],
        calendar_fn: CalendarFn,
    ):
        self.store = store
        self.manifest = manifest
        self.providers = providers
        self.calendar_fn = calendar_fn

    # ---------------- ingestion ----------------

    def ensure(
        self,
        symbols: Sequence[str],
        freq: Freq,
        start: datetime,
        end: datetime,
        provider_name: str,
        progress_cb: ProgressCb | None = None,
        chunk_days: int = _DEFAULT_CHUNK_DAYS,
    ) -> None:
        """Fetch+store only what's missing for `symbols` over [start, end]."""
        if provider_name not in self.providers:
            raise ProviderError(f"unknown provider '{provider_name}'", provider=provider_name)
        provider = self.providers[provider_name]
        calendar = self.calendar_fn(start, end)
        max_history_days = provider.capabilities.max_history_days

        total = len(symbols)
        for i, symbol in enumerate(symbols):
            gaps = self.store.missing_ranges(symbol, freq, start, end, calendar)
            for gap_start, gap_end in gaps:
                for chunk_start, chunk_end in _chunk_range(gap_start, gap_end, chunk_days, max_history_days):
                    req = BarRequest(symbols=[symbol], freq=freq, start=chunk_start, end=chunk_end)
                    try:
                        frame = provider.fetch_bars(req)
                    except ProviderError as e:
                        self.manifest.log_fetch(
                            symbol, freq, provider_name, chunk_start, chunk_end, 0, "error", detail=str(e)
                        )
                        raise
                    if frame.empty:
                        self.manifest.log_fetch(
                            symbol, freq, provider_name, chunk_start, chunk_end, 0, "empty"
                        )
                        continue
                    self.store.write(frame, freq, provider_name)
                    self.manifest.log_fetch(
                        symbol, freq, provider_name, chunk_start, chunk_end, len(frame), "ok"
                    )
            cov = self.store.coverage(symbol, freq)
            if cov is not None:
                self.manifest.upsert_coverage(cov)
            if progress_cb is not None:
                progress_cb(i + 1, total)

    # ---------------- assembly ----------------

    def load_context(
        self,
        symbols: Sequence[str],
        freq: Freq,
        start: datetime,
        end: datetime,
        instruments: Mapping[str, Instrument],
        universe: Universe | None = None,
        actions: Sequence[CorporateAction] = (),
        benchmark_symbol: str | None = None,
        delisting_return_pct: float | None = -0.30,
    ) -> DataContext:
        symbols = list(symbols)
        calendar = self.calendar_fn(start, end)

        req = BarRequest(symbols=symbols, freq=freq, start=start, end=end)
        bf = self.store.read(req)
        open_ = bf.wide("open").reindex(index=calendar, columns=symbols)
        high = bf.wide("high").reindex(index=calendar, columns=symbols)
        low = bf.wide("low").reindex(index=calendar, columns=symbols)
        close = bf.wide("close").reindex(index=calendar, columns=symbols)
        volume = bf.wide("volume").reindex(index=calendar, columns=symbols)
        value = bf.wide("value").reindex(index=calendar, columns=symbols)

        total_return = build_total_return(close, list(actions))

        if universe is not None:
            umask = universe.mask(calendar, symbols)
        else:
            umask = pd.DataFrame(True, index=calendar, columns=symbols)

        delisting = None
        if delisting_return_pct is not None:
            delisting = _build_delisting_frame(instruments, calendar, symbols, delisting_return_pct)

        benchmark = None
        if benchmark_symbol is not None:
            breq = BarRequest(symbols=[benchmark_symbol], freq=freq, start=start, end=end)
            bbf = self.store.read(breq)
            bclose = bbf.wide("close").reindex(index=calendar)
            if benchmark_symbol in bclose.columns:
                benchmark = bclose[benchmark_symbol]

        return DataContext(
            calendar=calendar,
            instruments=dict(instruments),
            open=open_,
            high=high,
            low=low,
            close=close,
            total_return=total_return,
            volume=volume,
            value=value,
            universe_mask=umask,
            delisting_return=delisting,
            freq=freq,
            events={},
            extras={},
            benchmark=benchmark,
        )


__all__ = ["DataService"]
