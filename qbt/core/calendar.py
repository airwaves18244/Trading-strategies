"""MOEX trading calendar (WS-A).

Two markets share one calendar: ``'stock'`` (equities/ETFs/bonds, main board)
and ``'forts'`` (derivatives). They differ only in the 2022 halt range — see
``HALT_RANGES`` — and are otherwise identical (same weekday + holiday rules).

Holiday-list imprecision (documented, not a bug):
Russia's government publishes a year-specific "production calendar" that
(a) lists the recurring public holidays below and (b) transfers individual
days off when a holiday lands on a weekend — sometimes to the very next
Monday, but sometimes to an unrelated day weeks or months away (e.g. bridging
a long weekend elsewhere). We only approximate case (a) plus the common
adjacent-Monday transfer for case (b). This will disagree with the *exact*
official calendar on a handful of scattered dates per year. Good enough for
backtesting (a handful of extra/missing trading days does not materially
move multi-year performance stats); not good enough for exchange-fidelity
settlement calculations.
"""
from __future__ import annotations

from datetime import date, timedelta
from functools import lru_cache

import pandas as pd

from qbt.core.types import to_utc

MARKETS: tuple[str, ...] = ("stock", "forts")

_FIRST_YEAR = 2010
_LAST_YEAR = 2026

#: (month, day) of MOEX's recurring official non-trading holidays (approximate,
#: see module docstring).
_FIXED_HOLIDAYS_MD: tuple[tuple[int, int], ...] = (
    (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 8),  # New Year + Orthodox Christmas block
    (2, 23),   # Defender of the Fatherland Day
    (3, 8),    # International Women's Day
    (5, 1),    # Spring and Labour Day
    (5, 9),    # Victory Day
    (6, 12),   # Russia Day
    (11, 4),   # Unity Day
)

#: 2022 sanctions-driven trading halt, both endpoints inclusive-closed.
#: Equity/stock market resumed (partially) 2022-03-24; FORTS derivatives
#: resumed earlier, 2022-03-21 (risk decision #1: calendar marks it, no masking
#: elsewhere).
HALT_RANGES: dict[str, tuple[date, date]] = {
    "stock": (date(2022, 2, 28), date(2022, 3, 24)),
    "forts": (date(2022, 2, 28), date(2022, 3, 21)),
}


def _check_market(market: str) -> None:
    if market not in MARKETS:
        raise ValueError(f"market must be one of {MARKETS}, got {market!r}")


@lru_cache(maxsize=None)
def _holidays_for_year(year: int) -> frozenset[date]:
    """Fixed holidays for `year`, plus an approximated adjacent-Monday weekend shift."""
    days: set[date] = set()
    for m, d in _FIXED_HOLIDAYS_MD:
        try:
            base = date(year, m, d)
        except ValueError:  # pragma: no cover - defensive, all (m,d) above are valid
            continue
        days.add(base)
        if base.weekday() == 5:  # Saturday -> following Monday also off
            days.add(base + timedelta(days=2))
        elif base.weekday() == 6:  # Sunday -> following Monday also off
            days.add(base + timedelta(days=1))
    return frozenset(days)


def _holidays_between(start_year: int, end_year: int) -> frozenset[date]:
    out: set[date] = set()
    lo = min(max(start_year, _FIRST_YEAR), _LAST_YEAR)
    hi = max(min(end_year, _LAST_YEAR), _FIRST_YEAR)
    for y in range(min(lo, start_year), max(hi, end_year) + 1):
        out |= _holidays_for_year(y)
    return frozenset(out)


def is_trading_day(day: date | pd.Timestamp | str, market: str = "stock") -> bool:
    """True if `day` is a MOEX trading day for `market` ('stock' | 'forts')."""
    _check_market(market)
    ts = to_utc(day).normalize()
    if ts.weekday() >= 5:
        return False
    d = ts.date()
    if d in _holidays_for_year(d.year):
        return False
    halt_start, halt_end = HALT_RANGES[market]
    if halt_start <= d <= halt_end:
        return False
    return True


def trading_days(
    start: date | pd.Timestamp | str,
    end: date | pd.Timestamp | str,
    market: str = "stock",
) -> pd.DatetimeIndex:
    """Trading days in [start, end], inclusive, as a UTC tz-aware DatetimeIndex."""
    _check_market(market)
    start_ts = to_utc(start).normalize()
    end_ts = to_utc(end).normalize()
    if end_ts < start_ts:
        return pd.DatetimeIndex([], tz="UTC")

    all_days = pd.date_range(start_ts, end_ts, freq="D", tz="UTC")
    business = all_days[all_days.weekday < 5]
    if len(business) == 0:
        return business

    holidays = _holidays_between(start_ts.year, end_ts.year)
    hol_index = pd.DatetimeIndex(sorted(holidays), tz="UTC")
    business = business[~business.isin(hol_index)]

    halt_start, halt_end = HALT_RANGES[market]
    halt_start_ts = to_utc(halt_start)
    halt_end_ts = to_utc(halt_end)
    business = business[~((business >= halt_start_ts) & (business <= halt_end_ts))]

    return business


__all__ = ["MARKETS", "HALT_RANGES", "is_trading_day", "trading_days"]
