"""Pydantic request/response models for the web/API layer.

These are the wire contracts between the UI (qbt/web) and the FastAPI routes
(qbt/api/routes_*.py). They are intentionally decoupled from the frozen
`BacktestResult`/`to_run_json` data contract (qbt/engine/result.py) and from
`StrategyMeta` (qbt/strategy/base.py) -- those are serialized ad hoc in the
routes, not modeled here, since they belong to other owners.
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class RunRequest(BaseModel):
    """Submits one backtest. Maps 1:1 to a Strategy + DataContext + engine run.

    `params` are validated against the strategy's `Param` specs by the
    strategy's own __init__ (qbt/strategy/base.py) -- this layer does not
    duplicate that validation, it only shapes the HTTP request.
    """

    model_config = ConfigDict(extra="forbid")

    strategy_key: str
    params: dict[str, Any] = Field(default_factory=dict)
    universe: str = "moex_liquid"
    start: str = "2015-01-01"
    end: str = "2023-12-29"
    freq: str = "1d"
    cost_preset: str = "moex_equity"
    execution_lag: int = 1
    overlay: str | None = None
    vol_target: float | None = None
    long_only: bool | None = None
    initial_nav: float = 1_000_000.0


class RunStatus(BaseModel):
    """Job status polled by the UI every ~1s while a run/sweep is in flight."""

    run_id: str
    state: Literal["queued", "running", "done", "error"]
    progress: float = 0.0
    error: str | None = None
    kind: str = "run"
    strategy_key: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class SweepRequest(RunRequest):
    """A RunRequest plus a parameter grid. 1-2 params expected (per engine spec)."""

    grid: dict[str, list[Any]]


class DataEnsureRequest(BaseModel):
    """POST /api/data/ensure body. Either `universe` or explicit `symbols`."""

    model_config = ConfigDict(extra="forbid")

    universe: str | None = None
    symbols: list[str] | None = None
    freq: str = "1d"
    start: str = "2015-01-01"
    end: str | None = None
    provider: str = "moex_iss"


class RunSubmitResponse(BaseModel):
    run_id: str


__all__ = [
    "RunRequest", "RunStatus", "SweepRequest", "DataEnsureRequest", "RunSubmitResponse",
]
