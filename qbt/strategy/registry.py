"""Auto-discovery strategy registry. PHASE 0 CONTRACT (fully implemented).

Every module in qbt.strategies is imported; every Strategy subclass with a `key`
ClassVar is registered. No hand-edited central list — parallel workstreams add
files without touching shared code.
"""
from __future__ import annotations

import importlib
import pkgutil

from qbt.strategy.base import Strategy, StrategyMeta

_REGISTRY: dict[str, type[Strategy]] | None = None


def _discover() -> dict[str, type[Strategy]]:
    import qbt.strategies as pkg

    for mod in pkgutil.iter_modules(pkg.__path__):
        if not mod.name.startswith("_"):
            importlib.import_module(f"qbt.strategies.{mod.name}")

    reg: dict[str, type[Strategy]] = {}

    def collect(cls: type[Strategy]) -> None:
        for sub in cls.__subclasses__():
            if (getattr(sub, "key", None) and not getattr(sub, "abstract", False)
                    and sub.__module__.startswith("qbt.strategies.")):
                if sub.key in reg and reg[sub.key] is not sub:
                    raise RuntimeError(f"Duplicate strategy key '{sub.key}': "
                                       f"{reg[sub.key].__module__} vs {sub.__module__}")
                reg[sub.key] = sub
            collect(sub)

    collect(Strategy)
    return reg


def all_strategies(refresh: bool = False) -> dict[str, type[Strategy]]:
    global _REGISTRY
    if _REGISTRY is None or refresh:
        _REGISTRY = _discover()
    return _REGISTRY


def get(key: str) -> type[Strategy]:
    reg = all_strategies()
    if key not in reg:
        raise KeyError(f"Unknown strategy '{key}'. Available: {sorted(reg)}")
    return reg[key]


def all_metas() -> list[StrategyMeta]:
    return sorted((cls.describe() for cls in all_strategies().values()), key=lambda m: m.key)
