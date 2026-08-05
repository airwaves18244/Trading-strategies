"""Universe implementations (WS-A): Static and point-in-time Index.

`LiquidityUniverse` is deferred per architecture.md.
"""
from __future__ import annotations

import bisect
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from qbt.core.errors import ConfigError
from qbt.core.types import to_utc

DEFAULT_UNIVERSE_DIR = Path("configs/universes")


@dataclass
class StaticUniverse:
    """Fixed symbol list, constant membership across all dates."""

    name: str
    symbols: Sequence[str]

    def members(self, asof: date | None = None) -> Sequence[str]:
        return list(self.symbols)

    def mask(self, calendar: pd.DatetimeIndex, symbols: Sequence[str]) -> pd.DataFrame:
        member = set(self.symbols)
        row = np.array([s in member for s in symbols], dtype=bool)
        data = np.broadcast_to(row, (len(calendar), len(symbols)))
        return pd.DataFrame(data, index=calendar, columns=list(symbols))


@dataclass
class IndexUniverse:
    """Point-in-time membership from periodic snapshots.

    `membership` is a long frame with columns [date, symbol]: each row means
    "symbol was a member as of this snapshot date". Membership is held
    constant (ffill) between consecutive snapshot dates.
    """

    name: str
    membership: pd.DataFrame
    _snapshots: list[pd.Timestamp] = field(init=False, repr=False, default_factory=list)
    _by_snapshot: dict[pd.Timestamp, frozenset[str]] = field(init=False, repr=False, default_factory=dict)

    def __post_init__(self) -> None:
        df = self.membership
        if "date" not in df.columns or "symbol" not in df.columns:
            raise ConfigError("IndexUniverse.membership needs columns ['date', 'symbol']")
        dates = pd.to_datetime(df["date"], utc=True)
        by: dict[pd.Timestamp, set[str]] = {}
        for d, sym in zip(dates, df["symbol"]):
            by.setdefault(d, set()).add(sym)
        self._snapshots = sorted(by)
        self._by_snapshot = {d: frozenset(s) for d, s in by.items()}

    def _members_asof_ts(self, ts: pd.Timestamp) -> frozenset[str]:
        if not self._snapshots:
            return frozenset()
        pos = bisect.bisect_right(self._snapshots, ts) - 1
        if pos < 0:
            return frozenset()
        return self._by_snapshot[self._snapshots[pos]]

    def members(self, asof: date) -> Sequence[str]:
        return sorted(self._members_asof_ts(to_utc(asof)))

    def mask(self, calendar: pd.DatetimeIndex, symbols: Sequence[str]) -> pd.DataFrame:
        symbols = list(symbols)
        out = np.zeros((len(calendar), len(symbols)), dtype=bool)
        for i, d in enumerate(calendar):
            members = self._members_asof_ts(d)
            if not members:
                continue
            out[i, :] = [s in members for s in symbols]
        return pd.DataFrame(out, index=calendar, columns=symbols)


#: Concrete implementations of qbt.data.interfaces.Universe shipped by WS-A.
UniverseImpl = StaticUniverse | IndexUniverse


def load_universe(name: str, base_dir: Path | str = DEFAULT_UNIVERSE_DIR) -> UniverseImpl:
    """Load `configs/universes/<name>.yaml`.

    Schema:
      ``{type: static, symbols: [...]}`` or
      ``{type: index, file: <path-to-parquet-or-csv, relative to base_dir if not absolute>}``
      (file has columns date, symbol).
    """
    base = Path(base_dir)
    cfg_path = base / f"{name}.yaml"
    if not cfg_path.exists():
        raise ConfigError(f"universe config not found: {cfg_path}")
    with cfg_path.open() as f:
        spec = yaml.safe_load(f) or {}

    kind = spec.get("type")
    if kind == "static":
        symbols = spec.get("symbols")
        if not symbols:
            raise ConfigError(f"universe '{name}': type=static requires non-empty 'symbols'")
        return StaticUniverse(name=name, symbols=list(symbols))

    if kind == "index":
        file_field = spec.get("file")
        if not file_field:
            raise ConfigError(f"universe '{name}': type=index requires a 'file' path")
        file_path = Path(file_field)
        if not file_path.is_absolute():
            file_path = base / file_path
        if not file_path.exists():
            raise ConfigError(f"universe '{name}': membership file not found: {file_path}")
        if file_path.suffix == ".parquet":
            membership = pd.read_parquet(file_path)
        else:
            membership = pd.read_csv(file_path)
        return IndexUniverse(name=name, membership=membership[["date", "symbol"]])

    raise ConfigError(f"universe '{name}': unknown type {kind!r} (expected 'static' or 'index')")


__all__ = ["StaticUniverse", "IndexUniverse", "UniverseImpl", "load_universe", "DEFAULT_UNIVERSE_DIR"]
