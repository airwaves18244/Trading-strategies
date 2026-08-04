"""Frozen core types. PHASE 0 CONTRACT — do not change signatures without updating docs/architecture.md.

All timestamps are UTC tz-aware. Bars are stored RAW; adjustment happens at read time.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum

import numpy as np
import pandas as pd


class AssetClass(StrEnum):
    EQUITY = "equity"
    FUTURE = "future"
    INDEX = "index"
    ETF = "etf"
    BOND = "bond"
    FX = "fx"
    CRYPTO = "crypto"


class Freq(StrEnum):
    D1 = "1d"
    H1 = "1h"
    M10 = "10m"
    M5 = "5m"
    M1 = "1m"


class PriceKind(StrEnum):
    RAW = "raw"            # as traded
    SPLIT_ADJ = "split"    # split-adjusted
    TOTAL_RETURN = "tr"    # dividends reinvested


class Session(StrEnum):
    MAIN = "main"   # canonical daily close = main-session close
    ALL = "all"     # includes MOEX evening session


@dataclass(frozen=True)
class Instrument:
    symbol: str                       # canonical: "MOEX:SBER", "MOEX:RTS" (continuous root)
    exchange: str
    asset_class: AssetClass
    currency: str = "RUB"
    board: str | None = None          # e.g. TQBR
    lot_size: int = 1
    tick_size: float = 0.01
    point_value: float = 1.0          # futures point value in currency
    listed_from: date | None = None
    listed_to: date | None = None     # set => delisted/expired
    sector: str | None = None
    shortable: bool = False           # post-2022 default: equities not shortable
    aliases: tuple[str, ...] = ()     # ticker renames: YNDX->YDEX etc.
    provider_symbols: Mapping[str, str] = field(default_factory=dict)
    # e.g. {"finam": "SBER@MISX", "moex_iss": "SBER", "algopack": "SBER"}


@dataclass(frozen=True)
class BarRequest:
    symbols: Sequence[str]
    freq: Freq
    start: datetime
    end: datetime
    price_kind: PriceKind = PriceKind.RAW
    session: Session = Session.MAIN


#: Long-format bar schema. ts is UTC tz-aware; value = turnover in currency; oi only for futures.
BAR_SCHEMA: tuple[str, ...] = ("symbol", "ts", "open", "high", "low", "close", "volume", "value", "oi")


class BarFrame:
    """Validated thin wrapper over a long DataFrame with BAR_SCHEMA columns."""

    def __init__(self, df: pd.DataFrame):
        self.df = df

    @classmethod
    def validate(cls, df: pd.DataFrame) -> "BarFrame":
        """Enforce schema: required columns, UTC tz-aware ts, numeric fields,
        (symbol, ts) dedup keep-last, sorted by (symbol, ts)."""
        missing = [c for c in BAR_SCHEMA if c not in df.columns]
        if missing:
            raise ValueError(f"BarFrame missing columns: {missing}")
        df = df.loc[:, list(BAR_SCHEMA)].copy()
        ts = pd.to_datetime(df["ts"], utc=True)
        df["ts"] = ts
        for col in ("open", "high", "low", "close", "volume", "value", "oi"):
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df["symbol"] = df["symbol"].astype(str)
        df = (
            df.sort_values(["symbol", "ts"])
            .drop_duplicates(subset=["symbol", "ts"], keep="last")
            .reset_index(drop=True)
        )
        return cls(df)

    def wide(self, fld: str) -> pd.DataFrame:
        """Pivot to wide format: index=ts, columns=symbol, values=field."""
        return self.df.pivot(index="ts", columns="symbol", values=fld).sort_index()

    def __len__(self) -> int:
        return len(self.df)

    @property
    def empty(self) -> bool:
        return self.df.empty

    @classmethod
    def empty_frame(cls) -> "BarFrame":
        return cls(pd.DataFrame({c: pd.Series(dtype="float64") if c not in ("symbol", "ts")
                                 else pd.Series(dtype="object") for c in BAR_SCHEMA}))

    def concat(self, other: "BarFrame") -> "BarFrame":
        return BarFrame.validate(pd.concat([self.df, other.df], ignore_index=True))


@dataclass(frozen=True)
class CorporateAction:
    symbol: str
    ex_date: date
    kind: str          # "div" | "split"
    value: float       # dividend per share (currency) or split ratio


@dataclass(frozen=True)
class FuturesContract:
    symbol: str            # e.g. "MOEX:RIH5"
    asset_code: str        # root, e.g. "RTS"
    start: date
    expiry: date
    point_value: float = 1.0


@dataclass(frozen=True)
class Coverage:
    symbol: str
    freq: Freq
    first_ts: datetime
    last_ts: datetime
    rows: int
    updated_at: datetime


def annualization_factor(freq: Freq) -> float:
    return {
        Freq.D1: 252.0,
        Freq.H1: 252.0 * 14,       # MOEX main+evening trading hours approx
        Freq.M10: 252.0 * 14 * 6,
        Freq.M5: 252.0 * 14 * 12,
        Freq.M1: 252.0 * 14 * 60,
    }[freq]


def to_utc(ts: datetime | pd.Timestamp | str) -> pd.Timestamp:
    t = pd.Timestamp(ts)
    return t.tz_localize("UTC") if t.tzinfo is None else t.tz_convert("UTC")


__all__ = [
    "AssetClass", "Freq", "PriceKind", "Session", "Instrument", "BarRequest",
    "BAR_SCHEMA", "BarFrame", "CorporateAction", "FuturesContract", "Coverage",
    "annualization_factor", "to_utc",
]
