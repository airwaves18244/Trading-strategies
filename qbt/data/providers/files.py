"""FileProvider: local CSV/parquet import — the seam for the user's existing FINAM_DATA
exports and any other pre-downloaded bars/events.

Two entry points:
  - load_bars(path, symbol=None) -> BarFrame       (flexible column-name mapping)
  - load_events(path, schema_name) -> pd.DataFrame  (qbt.data.schemas.validate_events)

Not a network provider: fetch_bars/list_instruments/etc. from MarketDataProvider exist only
so FileProvider can sit in the same registry and pass a health() check; they raise
ProviderError pointing callers at load_bars/load_events instead of silently returning
nothing.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

from qbt.core.errors import ProviderError
from qbt.core.types import (
    AssetClass, BarFrame, BarRequest, CorporateAction, Freq, FuturesContract, Instrument,
)
from qbt.data.interfaces import ProviderCapabilities, ProviderHealth
from qbt.data.schemas import validate_events

#: column-name aliases (case-insensitive, matched after stripping whitespace)
_COLUMN_ALIASES: dict[str, set[str]] = {
    "ts": {"date", "time", "datetime", "ts", "timestamp"},
    "open": {"open", "o"},
    "high": {"high", "h"},
    "low": {"low", "l"},
    "close": {"close", "c", "adj_close", "price"},
    "volume": {"volume", "vol", "v"},
    "value": {"value", "val", "turnover", "amount"},
    "oi": {"oi", "openinterest", "open_interest"},
    "symbol": {"symbol", "ticker", "secid", "sym"},
}


def _read_table(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix in (".parquet", ".pq"):
        return pd.read_parquet(path)
    if suffix in (".csv", ".txt"):
        return pd.read_csv(path)
    raise ProviderError(f"files: unsupported file extension '{suffix}' for {path}", provider="files")


def _detect_columns(columns: pd.Index) -> dict[str, str]:
    lower_map = {str(c).strip().lower(): c for c in columns}
    resolved: dict[str, str] = {}
    for target, aliases in _COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in lower_map:
                resolved[target] = lower_map[alias]
                break
    return resolved


class FileProvider:
    """Local CSV/parquet importer for bars and event tables."""

    name = "files"
    capabilities = ProviderCapabilities(
        freqs=frozenset({Freq.D1, Freq.H1, Freq.M10, Freq.M5, Freq.M1}),
        asset_classes=frozenset(AssetClass),
        max_history_days=None,
        pit_universe=False,
        corporate_actions=False,
        futures_chains=False,
        needs_key=False,
        rate_limit_per_min=None,
    )

    def __init__(self, base_dir: Path | str | None = None):
        self.base_dir = Path(base_dir) if base_dir is not None else None

    def _resolve(self, path: Path | str) -> Path:
        p = Path(path)
        if not p.is_absolute() and self.base_dir is not None:
            p = self.base_dir / p
        return p

    # -- bars -----------------------------------------------------------------

    def load_bars(self, path: Path | str, symbol: str | None = None) -> BarFrame:
        """Import a CSV/parquet file of bars. Column names are matched flexibly (see
        _COLUMN_ALIASES). `symbol` overrides any symbol column; if neither is present the
        file's stem (e.g. 'SBER.csv' -> 'SBER') is used for every row."""
        p = self._resolve(path)
        raw = _read_table(p)
        cols = _detect_columns(raw.columns)
        for required in ("ts", "open", "high", "low", "close"):
            if required not in cols:
                raise ProviderError(
                    f"files: {p} is missing a recognizable '{required}' column "
                    f"(looked for {sorted(_COLUMN_ALIASES[required])}); found columns: "
                    f"{list(raw.columns)}",
                    provider="files",
                )
        if symbol is not None:
            symbol_series = symbol
        elif "symbol" in cols:
            symbol_series = raw[cols["symbol"]].astype(str)
        else:
            symbol_series = p.stem

        out = pd.DataFrame({
            "symbol": symbol_series,
            "ts": pd.to_datetime(raw[cols["ts"]], utc=True),
            "open": pd.to_numeric(raw[cols["open"]], errors="coerce"),
            "high": pd.to_numeric(raw[cols["high"]], errors="coerce"),
            "low": pd.to_numeric(raw[cols["low"]], errors="coerce"),
            "close": pd.to_numeric(raw[cols["close"]], errors="coerce"),
            "volume": pd.to_numeric(raw[cols["volume"]], errors="coerce") if "volume" in cols else float("nan"),
            "value": pd.to_numeric(raw[cols["value"]], errors="coerce") if "value" in cols else float("nan"),
            "oi": pd.to_numeric(raw[cols["oi"]], errors="coerce") if "oi" in cols else float("nan"),
        })
        return BarFrame.validate(out)

    # -- events -----------------------------------------------------------------

    def load_events(self, path: Path | str, schema_name: str) -> pd.DataFrame:
        """Import a CSV/parquet event table and validate it against
        qbt.data.schemas.EVENT_SCHEMAS[schema_name]. Raises SchemaError on mismatch."""
        p = self._resolve(path)
        raw = _read_table(p)
        return validate_events(raw, schema_name)

    # -- MarketDataProvider protocol (network-shaped methods; not applicable) ------

    def fetch_bars(self, req: BarRequest) -> BarFrame:
        raise ProviderError(
            "FileProvider has no notion of a BarRequest fetch; call load_bars(path) directly",
            provider="files",
        )

    def list_instruments(
        self, asof: date | None = None, asset_class: AssetClass | None = None
    ) -> list[Instrument]:
        raise ProviderError("FileProvider does not list instruments", provider="files")

    def fetch_corporate_actions(self, symbol: str) -> list[CorporateAction]:
        raise ProviderError("FileProvider does not provide corporate actions", provider="files")

    def fetch_futures_chain(self, asset_code: str, include_expired: bool = True) -> list[FuturesContract]:
        raise ProviderError("FileProvider does not provide futures chains", provider="files")

    def health(self) -> ProviderHealth:
        ok = self.base_dir is None or self.base_dir.exists()
        detail = "local file importer; no live endpoint"
        if self.base_dir is not None and not ok:
            detail = f"base_dir does not exist: {self.base_dir}"
        return ProviderHealth(ok=ok, provider=self.name, detail=detail)


__all__ = ["FileProvider"]
