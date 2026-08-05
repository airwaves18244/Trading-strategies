"""sqlite coverage/fetch-log manifest (WS-A).

Lives at ``<cache_dir>/manifest.sqlite``. Two tables:

- ``coverage``: one row per (symbol, freq) summarizing what's in the parquet
  store — first/last ts, row count, when it was last updated. Overwritten
  wholesale on each ``upsert_coverage`` call (callers recompute the full
  Coverage from the store after a write, they don't hand us deltas).
- ``fetch_log``: append-only audit trail of provider fetch attempts.

WAL mode + per-thread connections
----------------------------------
The API job registry runs a ``ThreadPoolExecutor`` (architecture.md, WS-E) so
multiple worker threads may call into the same ``Manifest`` instance
concurrently. ``sqlite3.Connection`` objects are not safe to share across
threads (the C library enforces this; the default ``check_same_thread=True``
makes cross-thread use raise). Rather than pass ``check_same_thread=False``
and rely on external locking, each thread gets its own connection lazily
(via ``threading.local``), which sidesteps sharing entirely and keeps each
thread's transactions isolated. WAL (Write-Ahead Logging) mode is enabled so
readers don't block writers and multiple threads reading concurrently don't
serialize behind a single lock; a ``busy_timeout`` handles the brief
serialization SQLite still requires between concurrent *writers*.
"""
from __future__ import annotations

import sqlite3
import threading
from datetime import datetime
from pathlib import Path

import pandas as pd

from qbt.core.types import Coverage, Freq, to_utc

_SCHEMA = """
CREATE TABLE IF NOT EXISTS coverage (
    symbol TEXT NOT NULL,
    freq TEXT NOT NULL,
    first_ts TEXT NOT NULL,
    last_ts TEXT NOT NULL,
    rows INTEGER NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (symbol, freq)
);
CREATE TABLE IF NOT EXISTS fetch_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    freq TEXT NOT NULL,
    provider TEXT NOT NULL,
    start TEXT NOT NULL,
    end TEXT NOT NULL,
    rows INTEGER NOT NULL,
    status TEXT NOT NULL,
    detail TEXT NOT NULL DEFAULT '',
    logged_at TEXT NOT NULL
);
"""


def _iso(ts: datetime | pd.Timestamp | str) -> str:
    return to_utc(ts).isoformat()


class Manifest:
    def __init__(self, path: Path | str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        # touch the schema once from the constructing thread so callers that
        # only ever read (or never write) still get the tables.
        self._connect()

    def _connect(self) -> sqlite3.Connection:
        conn = getattr(self._local, "conn", None)
        if conn is None:
            conn = sqlite3.connect(str(self.path), timeout=30.0, check_same_thread=True)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA busy_timeout=30000")
            conn.executescript(_SCHEMA)
            conn.commit()
            self._local.conn = conn
        return conn

    def close(self) -> None:
        conn = getattr(self._local, "conn", None)
        if conn is not None:
            conn.close()
            self._local.conn = None

    # ---------------- coverage ----------------

    def upsert_coverage(self, coverage: Coverage) -> None:
        conn = self._connect()
        conn.execute(
            """
            INSERT INTO coverage (symbol, freq, first_ts, last_ts, rows, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(symbol, freq) DO UPDATE SET
                first_ts=excluded.first_ts,
                last_ts=excluded.last_ts,
                rows=excluded.rows,
                updated_at=excluded.updated_at
            """,
            (
                coverage.symbol,
                Freq(coverage.freq).value,
                _iso(coverage.first_ts),
                _iso(coverage.last_ts),
                int(coverage.rows),
                _iso(coverage.updated_at),
            ),
        )
        conn.commit()

    def get_coverage(self, symbol: str, freq: Freq) -> Coverage | None:
        conn = self._connect()
        row = conn.execute(
            "SELECT symbol, freq, first_ts, last_ts, rows, updated_at "
            "FROM coverage WHERE symbol=? AND freq=?",
            (symbol, Freq(freq).value),
        ).fetchone()
        if row is None:
            return None
        symbol_, freq_, first_ts, last_ts, rows, updated_at = row
        return Coverage(
            symbol=symbol_,
            freq=Freq(freq_),
            first_ts=to_utc(first_ts),
            last_ts=to_utc(last_ts),
            rows=int(rows),
            updated_at=to_utc(updated_at),
        )

    def all_coverage(self) -> list[Coverage]:
        conn = self._connect()
        rows = conn.execute(
            "SELECT symbol, freq, first_ts, last_ts, rows, updated_at FROM coverage"
        ).fetchall()
        return [
            Coverage(
                symbol=r[0], freq=Freq(r[1]), first_ts=to_utc(r[2]),
                last_ts=to_utc(r[3]), rows=int(r[4]), updated_at=to_utc(r[5]),
            )
            for r in rows
        ]

    # ---------------- fetch log ----------------

    def log_fetch(
        self,
        symbol: str,
        freq: Freq,
        provider: str,
        start: datetime,
        end: datetime,
        rows: int,
        status: str,
        detail: str = "",
    ) -> None:
        conn = self._connect()
        conn.execute(
            """
            INSERT INTO fetch_log (symbol, freq, provider, start, end, rows, status, detail, logged_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                symbol,
                Freq(freq).value,
                provider,
                _iso(start),
                _iso(end),
                int(rows),
                status,
                detail,
                pd.Timestamp.now(tz="UTC").isoformat(),
            ),
        )
        conn.commit()


__all__ = ["Manifest"]
