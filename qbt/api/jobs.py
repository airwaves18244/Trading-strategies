"""In-process job registry (WS-E).

Constraint: uvicorn MUST run with a single worker and without --reload — the
registry lives in this process. Results persist to runs/<run_id>/ so history
survives restarts (done runs are re-discovered from disk).
"""
from __future__ import annotations

import json
import shutil
import threading
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from qbt.engine.result import BacktestResult


class RunningJobError(Exception):
    """Raised by JobRegistry.delete() when the job is still queued/running."""


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
                                  "updated_at": _now(),
                                  # UI-editable / derived fields (section 2, API v2): default
                                  # here so every job row -- not just "run" kind -- has them,
                                  # then let explicit meta override if ever needed.
                                  "label": "", "starred": False, "summary": None,
                                  **(meta or {})}
            self._write_status(run_id)

        def progress(p: float) -> None:
            self._set(run_id, progress=round(min(max(p, 0.0), 1.0), 3), state="running")

        def work() -> None:
            self._set(run_id, state="running")
            try:
                out = fn(run_id, progress)
                d = self.runs_dir / run_id
                done_fields: dict[str, Any] = {}
                if isinstance(out, BacktestResult):
                    out.save(d)
                    # API v2: merge a small summary into status.json on completion so
                    # GET /api/runs can show a sharpe chip without loading the full result.
                    m = out.metrics or {}
                    done_fields["summary"] = {
                        "sharpe": m.get("sharpe"), "cagr": m.get("cagr"), "max_dd": m.get("max_dd"),
                    }
                elif isinstance(out, pd.DataFrame):
                    out.to_parquet(d / "sweep.parquet")
                elif out is not None:
                    (d / "output.json").write_text(json.dumps(out, default=str))
                self._set(run_id, state="done", progress=1.0, **done_fields)
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

    def patch(self, run_id: str, **fields: Any) -> dict[str, Any]:
        """Merge `fields` (e.g. label/starred) into status.json. Raises KeyError
        for an unknown run_id -- app.py maps that to 404."""
        with self._lock:
            if run_id not in self._jobs:
                raise KeyError(run_id)
            self._jobs[run_id].update(fields, updated_at=_now())
            self._write_status(run_id)
            return dict(self._jobs[run_id])

    def delete(self, run_id: str) -> None:
        """Remove the run's status entry + on-disk runs/<run_id> dir.

        Raises KeyError for an unknown run_id (-> 404) and RunningJobError if
        the job is still queued/running (-> 409); app.py maps both.
        """
        with self._lock:
            job = self._jobs.get(run_id)
            if job is None:
                raise KeyError(run_id)
            if job.get("state") in ("queued", "running"):
                raise RunningJobError(run_id)
            del self._jobs[run_id]
        d = self.runs_dir / run_id
        if d.exists():
            shutil.rmtree(d)
