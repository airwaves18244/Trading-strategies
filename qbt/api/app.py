"""FastAPI application factory (WS-E).

create_app(runner="fake"|"real"|instance). Single worker, no --reload (see jobs.py).
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader

from qbt.api.jobs import JobRegistry
from qbt.api.schemas import DataEnsureRequest, RunRequest, RunSubmitResponse, SweepRequest
from qbt.engine.result import BacktestResult

_WEB = Path(__file__).resolve().parent.parent / "web"
_REPO = Path(__file__).resolve().parents[2]


def _strategy_metas() -> list[dict[str, Any]]:
    from qbt.strategy import registry
    metas = []
    for m in registry.all_metas():
        metas.append({
            "key": m.key, "name": m.name, "group": m.group,
            "data_required": m.data_required, "data_requirements": list(m.data_requirements),
            "output": m.output, "freq": m.freq, "default_universe": m.default_universe,
            "doc_path": m.doc_path, "description": m.description,
            "category": m.doc_path.split("/")[1] if "/" in m.doc_path else "",
            "params": [{
                "name": p.name, "default": p.default, "low": p.low, "high": p.high,
                "step": p.step, "choices": list(p.choices) if p.choices else None,
                "doc": p.doc, "source": p.source,
            } for p in m.params],
        })
    return metas


def _extract_section(md_path: Path, header_prefix: str = "## 3.") -> str:
    if not md_path.exists():
        return ""
    lines, out, on = md_path.read_text().splitlines(), [], False
    for ln in lines:
        if ln.startswith("## "):
            on = ln.startswith(header_prefix)
            if on:
                out.append(ln)
            continue
        if on:
            out.append(ln)
    return "\n".join(out)


def create_app(runner: Any = "fake", runs_dir: Path | None = None) -> FastAPI:
    if runner == "fake":
        from qbt.api.fake import FakeRunner
        runner = FakeRunner()
    elif runner == "real":
        from qbt.api.real import RealRunner
        runner = RealRunner()

    from qbt.core.config import get_settings
    rd = Path(runs_dir or get_settings().runs_dir)
    jobs = JobRegistry(rd)
    app = FastAPI(title="qbt terminal", version="0.1.0")
    app.state.runner = runner
    app.state.jobs = jobs

    app.mount("/static", StaticFiles(directory=_WEB / "static"), name="static")
    jinja = Environment(loader=FileSystemLoader(_WEB / "templates"), autoescape=False)

    @app.get("/", response_class=HTMLResponse)
    def index() -> str:
        return jinja.get_template("index.html").render(runner=getattr(runner, "name", "?"))

    # ---------------- strategies ----------------

    @app.get("/api/strategies")
    def strategies() -> list[dict[str, Any]]:
        return _strategy_metas()

    @app.get("/api/strategies/{key}/doc")
    def strategy_doc(key: str, section: str = "3") -> dict[str, str]:
        from qbt.strategy import registry
        try:
            cls = registry.get(key)
        except KeyError:
            raise HTTPException(404, f"unknown strategy {key}")
        md = _extract_section(_REPO / cls.doc_path, f"## {section}.")
        return {"markdown": md, "doc_path": cls.doc_path}

    # ---------------- runs ----------------

    @app.post("/api/runs", response_model=RunSubmitResponse)
    def submit_run(req: RunRequest) -> RunSubmitResponse:
        rid = jobs.submit("run", lambda run_id, cb: runner.run(req, run_id, cb),
                          meta={"strategy_key": req.strategy_key,
                                "request": req.model_dump()})
        return RunSubmitResponse(run_id=rid)

    @app.get("/api/runs")
    def list_runs() -> list[dict[str, Any]]:
        return jobs.list(kind="run")

    @app.get("/api/runs/{run_id}")
    def run_status(run_id: str) -> dict[str, Any]:
        st = jobs.status(run_id)
        if st is None:
            raise HTTPException(404, "unknown run")
        return st

    @app.get("/api/runs/{run_id}/result")
    def run_result(run_id: str, max_points: int = 3000) -> JSONResponse:
        st = jobs.status(run_id)
        if st is None:
            raise HTTPException(404, "unknown run")
        if st["state"] != "done":
            raise HTTPException(409, f"run is {st['state']}")
        res = BacktestResult.load(jobs.result_dir(run_id))
        return JSONResponse(res.to_run_json(max_points=max_points))

    # ---------------- sweeps ----------------

    @app.post("/api/sweeps", response_model=RunSubmitResponse)
    def submit_sweep(req: SweepRequest) -> RunSubmitResponse:
        rid = jobs.submit("sweep", lambda run_id, cb: runner.sweep(req, run_id, cb),
                          meta={"strategy_key": req.strategy_key,
                                "request": req.model_dump()})
        return RunSubmitResponse(run_id=rid)

    @app.get("/api/sweeps/{run_id}")
    def sweep_result(run_id: str) -> dict[str, Any]:
        st = jobs.status(run_id)
        if st is None:
            raise HTTPException(404, "unknown sweep")
        out: dict[str, Any] = dict(st)
        f = jobs.result_dir(run_id) / "sweep.parquet"
        if st["state"] == "done" and f.exists():
            df = pd.read_parquet(f)
            out["rows"] = json.loads(df.to_json(orient="records"))
        return out

    # ---------------- data ----------------

    @app.get("/api/data/status")
    def data_status() -> list[dict[str, Any]]:
        return runner.data_status()

    @app.get("/api/data/health")
    def data_health() -> list[dict[str, Any]]:
        return runner.data_health()

    @app.post("/api/data/ensure", response_model=RunSubmitResponse)
    def data_ensure(req: DataEnsureRequest) -> RunSubmitResponse:
        rid = jobs.submit("ensure", lambda run_id, cb: runner.ensure(req, cb),
                          meta={"request": req.model_dump()})
        return RunSubmitResponse(run_id=rid)

    @app.get("/api/bars")
    def bars(symbol: str, freq: str = "1d",
             start: str = "2015-01-01", end: str = "2026-01-01") -> list[dict[str, Any]]:
        return runner.bars(symbol, freq, start, end)

    @app.get("/api/universes")
    def universes() -> list[str]:
        d = _REPO / "configs" / "universes"
        return sorted(p.stem for p in d.glob("*.yaml")) if d.exists() else []

    return app
