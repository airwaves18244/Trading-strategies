"""In-process job registry (WS-E).

Constraint: uvicorn MUST run with a single worker and without --reload — the
registry lives in this process. Results persist to runs/<run_id>/ so history
survives restarts (done runs are re-discovered from disk).
"""
from __future__ import annotations

import json
import threading
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from qbt.engine.result import BacktestResult


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class JobRegistry:
    def __init__(self, runs_dir: Path, max_workers: int = 2):
        self.runs_dir = Path(runs_dir)
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        self._pool = ThreadPoolExecutor(max_workers=max_workers)
        self._lock = threading.Lock()
        self._jobs: dict[str, dict[str, Any]] = {}
        self._scan_disk()

    def _scan_disk(self) -> None:
        for d in self.runs_dir.iterdir() if self.runs_dir.exists() else []:
            st = d / "status.json"
            if st.exists():
                try:
                    self._jobs[d.name] = json.loads(st.read_text())
                except Exception:  # noqa: BLE001
                    continue

    def _write_status(self, run_id: str) -> None:
        d = self.runs_dir / run_id
        d.mkdir(parents=True, exist_ok=True)
        (d / "status.json").write_text(json.dumps(self._jobs[run_id], default=str))

    def _set(self, run_id: str, **kw: Any) -> None:
        with self._lock:
            self._jobs[run_id].update(kw, updated_at=_now())
            self._write_status(run_id)

    def submit(self, kind: str, fn: Callable[[str, Callable[[float], None]], Any],
               meta: dict[str, Any] | None = None) -> str:
        run_id = uuid.uuid4().hex[:12]
        with self._lock:
            self._jobs[run_id] = {"run_id": run_id, "state": "queued", "progress": 0.0,
                                  "error": None, "kind": kind, "created_at": _now(),
                                  "updated_at": _now(), **(meta or {})}
            self._write_status(run_id)

        def progress(p: float) -> None:
            self._set(run_id, progress=round(min(max(p, 0.0), 1.0), 3), state="running")

        def work() -> None:
            self._set(run_id, state="running")
            try:
                out = fn(run_id, progress)
                d = self.runs_dir / run_id
                if isinstance(out, BacktestResult):
                    out.save(d)
                elif isinstance(out, pd.DataFrame):
                    out.to_parquet(d / "sweep.parquet")
                elif out is not None:
                    (d / "output.json").write_text(json.dumps(out, default=str))
                self._set(run_id, state="done", progress=1.0)
            except Exception as e:  # noqa: BLE001
                self._set(run_id, state="error",
                          error=f"{type(e).__name__}: {e}",
                          trace=traceback.format_exc()[-4000:])

        self._pool.submit(work)
        return run_id

    def status(self, run_id: str) -> dict[str, Any] | None:
        with self._lock:
            return dict(self._jobs[run_id]) if run_id in self._jobs else None

    def list(self, kind: str | None = None) -> list[dict[str, Any]]:
        with self._lock:
            rows = [dict(v) for v in self._jobs.values() if kind is None or v.get("kind") == kind]
        return sorted(rows, key=lambda r: r.get("created_at", ""), reverse=True)

    def result_dir(self, run_id: str) -> Path:
        return self.runs_dir / run_id
