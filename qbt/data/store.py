"""ParquetBarStore — the BarStore protocol implementation (WS-A).

Layout: ``<root>/bars/freq=<freq>/symbol=<SYM_SANITIZED>/data.parquet``.
Symbols are sanitized for the filesystem by replacing ``:`` with ``_``
(canonical symbols look like ``MOEX:SBER``). Stores RAW prices only;
adjustment happens at read time (qbt/data/adjust.py).

Writes are atomic per symbol: merge new rows into any existing parquet,
dedup ``(symbol, ts)`` keep-last, write to a ``.tmp`` file, then
``os.replace`` it onto the real path (atomic on POSIX and Windows NTFS).
"""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

import pandas as pd

from qbt.core.types import BarFrame, BarRequest, Coverage, Freq, to_utc


def sanitize_symbol(symbol: str) -> str:
    return symbol.replace(":", "_")


class ParquetBarStore:
    """Parquet-backed bar cache rooted at `root` (typically Settings.cache_dir)."""

    def __init__(self, root: Path | str):
        self.root = Path(root)

    def _symbol_dir(self, symbol: str, freq: Freq) -> Path:
        return self.root / "bars" / f"freq={freq.value}" / f"symbol={sanitize_symbol(symbol)}"

    def _path(self, symbol: str, freq: Freq) -> Path:
        return self._symbol_dir(symbol, freq) / "data.parquet"

    # ---------------- BarStore protocol ----------------

    def read(self, req: BarRequest) -> BarFrame:
        frames: list[pd.DataFrame] = []
        for symbol in req.symbols:
            path = self._path(symbol, req.freq)
            if not path.exists():
                continue
            frames.append(pd.read_parquet(path))
        if not frames:
            return BarFrame.empty_frame()

        df = pd.concat(frames, ignore_index=True)
        df["ts"] = pd.to_datetime(df["ts"], utc=True)
        start = to_utc(req.start)
        end = to_utc(req.end)
        df = df[
            (df["ts"] >= start) & (df["ts"] <= end) & (df["symbol"].isin(list(req.symbols)))
        ]
        return BarFrame.validate(df)

    def write(self, frame: BarFrame, freq: Freq, provider: str) -> None:
        if frame.empty:
            return
        for symbol, sub in frame.df.groupby("symbol", sort=False):
            path = self._path(symbol, freq)
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                existing = pd.read_parquet(path)
                merged_raw = pd.concat([existing, sub], ignore_index=True)
            else:
                merged_raw = sub
            merged = BarFrame.validate(merged_raw).df
            tmp = path.with_suffix(".parquet.tmp")
            merged.to_parquet(tmp, index=False)
            os.replace(tmp, path)  # atomic within the same filesystem

    def coverage(self, symbol: str, freq: Freq) -> Coverage | None:
        path = self._path(symbol, freq)
        if not path.exists():
            return None
        df = pd.read_parquet(path, columns=["ts"])
        if df.empty:
            return None
        ts = pd.to_datetime(df["ts"], utc=True)
        return Coverage(
            symbol=symbol,
            freq=freq,
            first_ts=ts.min(),
            last_ts=ts.max(),
            rows=len(df),
            updated_at=pd.Timestamp.now(tz="UTC"),
        )

    def missing_ranges(
        self,
        symbol: str,
        freq: Freq,
        start: datetime,
        end: datetime,
        calendar: pd.DatetimeIndex,
    ) -> list[tuple[datetime, datetime]]:
        start_ts = to_utc(start)
        end_ts = to_utc(end)
        cal = calendar[(calendar >= start_ts) & (calendar <= end_ts)]
        if len(cal) == 0:
            return []

        path = self._path(symbol, freq)
        if path.exists():
            existing_ts = pd.to_datetime(pd.read_parquet(path, columns=["ts"])["ts"], utc=True)
            existing_days = set(existing_ts.normalize())
        else:
            existing_days = set()

        ranges: list[tuple[datetime, datetime]] = []
        run_start: pd.Timestamp | None = None
        prev: pd.Timestamp | None = None
        for d in cal:
            if d.normalize() not in existing_days:
                if run_start is None:
                    run_start = d
                prev = d
            else:
                if run_start is not None:
                    ranges.append((run_start, prev))
                    run_start = None
        if run_start is not None:
            ranges.append((run_start, prev))
        return ranges


__all__ = ["ParquetBarStore", "sanitize_symbol"]
