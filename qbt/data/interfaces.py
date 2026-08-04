"""Data-layer protocols. PHASE 0 CONTRACT.

Implementations: qbt/data/store.py (WS-A), qbt/data/providers/* (WS-B).
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime
from typing import ClassVar, Protocol, runtime_checkable

import pandas as pd

from qbt.core.types import (
    AssetClass, BarFrame, BarRequest, CorporateAction, Coverage, Freq,
    FuturesContract, Instrument,
)


@dataclass(frozen=True)
class ProviderCapabilities:
    freqs: frozenset[Freq]
    asset_classes: frozenset[AssetClass]
    max_history_days: int | None      # None = unbounded
    pit_universe: bool                # can list instruments as of a past date
    corporate_actions: bool
    futures_chains: bool
    needs_key: bool
    rate_limit_per_min: int | None


@dataclass(frozen=True)
class ProviderHealth:
    ok: bool
    provider: str
    detail: str = ""                  # human-readable: key present? sample fetch ok?


@runtime_checkable
class MarketDataProvider(Protocol):
    """One per data source. All returned bars must pass BarFrame.validate."""

    name: ClassVar[str]
    capabilities: ClassVar[ProviderCapabilities]

    def list_instruments(
        self, asof: date | None = None, asset_class: AssetClass | None = None
    ) -> list[Instrument]: ...

    def fetch_bars(self, req: BarRequest) -> BarFrame: ...

    def fetch_corporate_actions(self, symbol: str) -> list[CorporateAction]: ...

    def fetch_futures_chain(
        self, asset_code: str, include_expired: bool = True
    ) -> list[FuturesContract]: ...

    def health(self) -> ProviderHealth: ...


@runtime_checkable
class BarStore(Protocol):
    """Parquet-backed bar cache. Stores RAW prices only; adjustment at read time."""

    def read(self, req: BarRequest) -> BarFrame: ...

    def write(self, frame: BarFrame, freq: Freq, provider: str) -> None: ...

    def coverage(self, symbol: str, freq: Freq) -> Coverage | None: ...

    def missing_ranges(
        self, symbol: str, freq: Freq, start: datetime, end: datetime,
        calendar: pd.DatetimeIndex,
    ) -> list[tuple[datetime, datetime]]: ...


class Universe(Protocol):
    """Point-in-time membership. mask() aligns to a calendar index."""

    name: str

    def members(self, asof: date) -> Sequence[str]: ...

    def mask(self, calendar: pd.DatetimeIndex, symbols: Sequence[str]) -> pd.DataFrame: ...
