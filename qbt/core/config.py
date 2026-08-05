"""Application settings (WS-A).

Loads from environment variables prefixed ``QBT_`` and from a local ``.env``
file (via pydantic-settings' built-in dotenv support). Not a Phase 0 contract
file — safe to extend, but keep field names stable since CLI/API/tests read
them by name.
"""
from __future__ import annotations

import os
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_cache_dir() -> Path:
    """%LOCALAPPDATA%/qbt on Windows, else ~/.cache/qbt (risk decision #5)."""
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA")
        if base:
            return Path(base) / "qbt"
        return Path.home() / "AppData" / "Local" / "qbt"
    return Path.home() / ".cache" / "qbt"


class Settings(BaseSettings):
    """QBT_-prefixed settings, loaded from env and `.env`.

    Construct fresh (``Settings()``) rather than caching a module-level
    singleton so tests can monkeypatch env vars and get a clean read.
    """

    model_config = SettingsConfigDict(
        env_prefix="QBT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    #: Finam Trade API secret (user-supplied); REST-only, secret -> short-lived JWT (WS-B).
    finam_secret: str | None = None
    #: MOEX ALGOPACK token (user-supplied).
    algopack_token: str | None = None
    #: Parquet bar cache + sqlite manifest root.
    cache_dir: Path = Field(default_factory=_default_cache_dir)
    #: Backtest run outputs (runs/<run_id>/...).
    runs_dir: Path = Field(default=Path("runs"))
    #: Assumed return applied on a symbol's last trading day when it is
    #: suspended/delisted without a clean corporate-action price (risk decision #3).
    delisting_return_pct: float = -0.30


__all__ = ["Settings"]


def get_settings() -> Settings:
    """Convenience accessor; constructs fresh (see class docstring)."""
    return Settings()


__all__ = ["Settings", "get_settings"]
