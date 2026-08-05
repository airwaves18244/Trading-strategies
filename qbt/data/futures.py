"""Continuous futures construction (WS-A).

`RollRule` + `build_continuous` stitch a chain of discrete `FuturesContract`
bars into one `ContinuousSeries`:

- `.price` is the naive/unadjusted stitched level (whichever contract is
  held on a given date, at its own raw close) — it always shows the basis
  jump at a roll, regardless of `RollRule.adjustment`.
- `.ret` is built to be roll-jump-free for `adjustment in ('difference',
  'ratio')`: on the day the held contract switches, the return is computed
  from the *new* contract's own two most recent closes (a genuine
  within-contract return), not from the old contract's close vs. the new
  contract's close (which would embed the basis as a fake one-day return).
  For `adjustment='none'`, the roll-day return is left naive (front-to-back
  stitched price change), i.e. the jump is intentionally NOT removed — that's
  what "no adjustment" means here.
- `.held` names the contract symbol in force on each date; `.roll_dates`
  lists the dates a switch happened.

Note: `.ret` is a percentage return series throughout, so 'difference' and
'ratio' produce identical numbers under this convention — the distinction
between additive vs. multiplicative back-adjustment only matters when you
also expose an *adjusted price level* series, which this contract
deliberately does not (`.price` is always the raw stitched level). Both
options are accepted (and both remove the roll jump from `.ret`) so callers
can pick the one matching their mental model / a future adjusted-level
extension.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

import numpy as np
import pandas as pd

from qbt.core.types import BarFrame, FuturesContract

_METHODS = ("oi", "volume", "days_before_expiry")
_ADJUSTMENTS = ("difference", "ratio", "none")


@dataclass(frozen=True)
class RollRule:
    method: str  # 'oi' | 'volume' | 'days_before_expiry'
    offset_days: int = 3
    adjustment: str = "none"  # 'difference' | 'ratio' | 'none'

    def __post_init__(self) -> None:
        if self.method not in _METHODS:
            raise ValueError(f"method must be one of {_METHODS}, got {self.method!r}")
        if self.adjustment not in _ADJUSTMENTS:
            raise ValueError(f"adjustment must be one of {_ADJUSTMENTS}, got {self.adjustment!r}")
        if self.offset_days < 0:
            raise ValueError("offset_days must be >= 0")


@dataclass
class ContinuousSeries:
    price: pd.Series          # unadjusted stitched level
    ret: pd.Series             # within-contract pct returns, stitched
    held: pd.Series            # contract symbol held per date
    roll_dates: pd.DatetimeIndex


def build_continuous(chain: list[FuturesContract], bars: BarFrame, rule: RollRule) -> ContinuousSeries:
    if not chain:
        raise ValueError("chain must have at least one contract")
    contracts = sorted(chain, key=lambda c: c.expiry)

    close = bars.wide("close")
    oi = bars.wide("oi") if rule.method == "oi" else None
    vol = bars.wide("volume") if rule.method == "volume" else None

    dates = close.index.sort_values()
    if len(dates) == 0:
        empty = pd.Series(dtype=float)
        return ContinuousSeries(price=empty, ret=empty, held=pd.Series(dtype=object),
                                 roll_dates=pd.DatetimeIndex([], tz="UTC"))

    idx = 0
    cur = contracts[idx]
    consec = 0
    held_syms: list[str] = []
    roll_dates: list[pd.Timestamp] = []

    for d in dates:
        if idx < len(contracts) - 1:
            deadline = cur.expiry - timedelta(days=rule.offset_days)
            trigger = d.date() >= deadline
            if not trigger and rule.method in ("oi", "volume"):
                nxt = contracts[idx + 1]
                frame = oi if rule.method == "oi" else vol
                cur_v = frame.at[d, cur.symbol] if (cur.symbol in frame.columns and d in frame.index) else np.nan
                nxt_v = frame.at[d, nxt.symbol] if (nxt.symbol in frame.columns and d in frame.index) else np.nan
                if pd.notna(cur_v) and pd.notna(nxt_v) and nxt_v > cur_v:
                    consec += 1
                else:
                    consec = 0
                trigger = consec >= 2
            if trigger:
                idx += 1
                cur = contracts[idx]
                consec = 0
                roll_dates.append(d)
        held_syms.append(cur.symbol)

    held = pd.Series(held_syms, index=dates)

    price = pd.Series(index=dates, dtype=float)
    for d, sym in held.items():
        price[d] = close.at[d, sym] if (sym in close.columns and d in close.index) else np.nan

    ret = pd.Series(index=dates, dtype=float, name="ret")
    for i in range(1, len(dates)):
        d, d_prev = dates[i], dates[i - 1]
        sym_today = held.iloc[i]
        sym_prev = held.iloc[i - 1]
        is_roll = sym_today != sym_prev
        if is_roll and rule.adjustment != "none":
            # within-contract return: new contract's own prior close
            p0 = close.at[d_prev, sym_today] if (sym_today in close.columns and d_prev in close.index) else np.nan
        elif is_roll:  # adjustment == 'none': naive stitched jump, intentional
            p0 = price.iloc[i - 1]
        else:
            p0 = close.at[d_prev, sym_today] if (sym_today in close.columns) else np.nan
        p1 = close.at[d, sym_today] if sym_today in close.columns else np.nan
        if pd.notna(p0) and p0 != 0 and pd.notna(p1):
            ret.iloc[i] = p1 / p0 - 1.0

    return ContinuousSeries(
        price=price,
        ret=ret,
        held=held,
        roll_dates=pd.DatetimeIndex(roll_dates, tz="UTC") if roll_dates else pd.DatetimeIndex([], tz="UTC"),
    )


__all__ = ["RollRule", "ContinuousSeries", "build_continuous"]
