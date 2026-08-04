"""Synthetic data generators with analytic answers. PHASE 0 signatures; bodies = WS-C (engine).

Shared by every workstream's tests. make_context() is the standard way to get a
DataContext without any network/provider.
"""
from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from qbt.core.types import Freq
from qbt.engine.context import DataContext


def business_calendar(start: str, end: str) -> pd.DatetimeIndex:
    """UTC business-day calendar (no MOEX holidays — synthetic)."""
    return pd.bdate_range(start, end, tz="UTC")


def make_context(
    n_symbols: int = 5,
    start: str = "2015-01-05",
    end: str = "2023-12-29",
    drift: float | list[float] = 0.0002,
    vol: float | list[float] = 0.01,
    seed: int = 7,
    freq: Freq = Freq.D1,
) -> DataContext:
    """GBM-ish random universe, full universe_mask, volume/value filled,
    total_return == close (no dividends). Deterministic under seed."""
    raise NotImplementedError  # WS-C


def constant_drift_context(mu_daily: float = 0.001, n_days: int = 500) -> DataContext:
    """Single symbol, exact constant simple return each bar: closed-form equity
    (1+mu)^t for buy-and-hold — the analytic anchor for engine tests."""
    raise NotImplementedError  # WS-C


def piecewise_vol_context(vols: tuple[float, ...] = (0.005, 0.02), block: int = 120) -> DataContext:
    """Vol regime blocks — vol-target exposure must equal target/realized at
    known dates (up to estimator lag)."""
    raise NotImplementedError  # WS-C


def sawtooth_pair_context(period: int = 20, amp: float = 0.05) -> DataContext:
    """Two cointegrated series with deterministic sawtooth spread — pairs
    strategy must enter/exit on enumerable dates; PnL hand-computable."""
    raise NotImplementedError  # WS-C

def bid_ask_bounce_context(half_spread: float = 0.005, n_days: int = 750) -> DataContext:
    """Flat mid with alternating trade prints at bid/ask: reversal signals on
    trade prices show fake alpha that MUST die under one-day-wait execution —
    the deterministic ground for the lag canary."""
    raise NotImplementedError  # WS-C


def known_drawdown_context() -> tuple[DataContext, dict[str, float]]:
    """Hand-built path with known max_dd, dd duration and per-year numbers;
    returns (ctx, expected_metrics)."""
    raise NotImplementedError  # WS-C


def event_fixture(schema_name: str, symbols: list[str], calendar: pd.DatetimeIndex,
                  n_events: int = 12, seed: int = 7) -> pd.DataFrame:
    """Generate a valid synthetic event table for any EVENT_SCHEMAS entry, so
    Group B/C strategies run green with zero user data."""
    raise NotImplementedError  # WS-C
