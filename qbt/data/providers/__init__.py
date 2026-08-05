"""Provider registry.

PROVIDERS maps a short provider name to its class. make_provider(name, settings) builds an
instance, wiring credentials from a settings-like object. `settings` is duck-typed
(attributes `finam_secret` / `algopack_token`) — WS-A's qbt.core.config.Settings will
satisfy this once it exists, but this module does not import it, to avoid a cross-workstream
dependency before Phase 0 lands.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from qbt.core.errors import ConfigError
from qbt.data.providers.algopack import AlgopackProvider
from qbt.data.providers.files import FileProvider
from qbt.data.providers.finam import FinamProvider
from qbt.data.providers.moex_iss import MoexIssProvider

PROVIDERS: dict[str, type] = {
    "moex_iss": MoexIssProvider,
    "algopack": AlgopackProvider,
    "finam": FinamProvider,
    "files": FileProvider,
}

#: configs/instruments/moex_aliases.yaml, relative to the repo root (.../qbt/data/providers/__init__.py
#: is 3 levels below the root: providers -> data -> qbt -> <root>).
_DEFAULT_ALIASES_PATH = Path(__file__).resolve().parents[3] / "configs" / "instruments" / "moex_aliases.yaml"


def load_aliases(path: Path | str | None = None) -> dict[str, str | None]:
    """Load the ticker-rename alias map (YNDX->YDEX etc.) from
    configs/instruments/moex_aliases.yaml. Returns {old_ticker: new_ticker_or_None};
    None means "delisted, no MOEX successor" (see POLY). Missing file -> {}."""
    p = Path(path) if path is not None else _DEFAULT_ALIASES_PATH
    if not p.exists():
        return {}
    with p.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    aliases = raw.get("aliases", raw) if isinstance(raw, dict) else {}
    return dict(aliases)


def make_provider(name: str, settings: Any = None):
    """Instantiate a provider by registry name.

    `settings`, if given, is any object exposing `.finam_secret` / `.algopack_token`
    attributes (falsy/missing => ConfigError for providers that need_key). moex_iss and
    files need no credentials and ignore `settings`.
    """
    if name not in PROVIDERS:
        raise ConfigError(f"Unknown provider '{name}'. Known providers: {sorted(PROVIDERS)}")
    cls = PROVIDERS[name]

    if name == "moex_iss":
        return cls()
    if name == "files":
        base_dir = getattr(settings, "files_base_dir", None) if settings is not None else None
        return cls(base_dir=base_dir)
    if name == "finam":
        secret = getattr(settings, "finam_secret", None) if settings is not None else None
        if not secret:
            raise ConfigError(
                "Provider 'finam' requires a 'finam_secret' attribute on `settings` "
                "(QBT_FINAM_SECRET in .env)."
            )
        return cls(secret=secret)
    if name == "algopack":
        token = getattr(settings, "algopack_token", None) if settings is not None else None
        if not token:
            raise ConfigError(
                "Provider 'algopack' requires an 'algopack_token' attribute on `settings` "
                "(QBT_ALGOPACK_TOKEN in .env)."
            )
        return cls(token=token)
    raise ConfigError(f"No construction wiring registered for provider '{name}'")  # pragma: no cover


__all__ = ["PROVIDERS", "make_provider", "load_aliases"]
