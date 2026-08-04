"""Strategy API. PHASE 0 CONTRACT (fully implemented).

A strategy is one file in qbt/strategies/, subclassing Strategy, discovered
automatically by qbt.strategy.registry. Strategies see ONLY a DataContext.

Two output modes:
  - "weights": generate() returns a DataFrame (index=calendar, columns=symbols)
    of target weights BEFORE execution lag; the runner applies
    shift_for_execution, risk caps, vol targeting, overlays and the cost model.
    generate() MAY loop internally (state machines are fine) — "weights" does
    not imply vectorized-only.
  - "orders": generate() returns list[OrderIntent]; the OrderEngine resolves
    sizing (size_mode) against runtime NAV, simulates stops/takes/time exits
    with conservative fills. Risk overlays do NOT apply to order strategies;
    sizing is embedded in the intents.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, ClassVar, Literal, Protocol, runtime_checkable

import pandas as pd

from qbt.core.types import Freq
from qbt.engine.context import DataContext


@dataclass(frozen=True)
class Param:
    name: str
    default: Any
    low: float | None = None
    high: float | None = None
    step: float | None = None
    choices: tuple[Any, ...] | None = None
    doc: str = ""
    source: str = ""     # reference into the research corpus, e.g. "02-momentum/02 §3"


@dataclass(frozen=True)
class OrderIntent:
    ts: pd.Timestamp
    symbol: str
    side: int                                  # +1 long, -1 short
    size_mode: Literal["risk_frac", "nav_frac", "target_weight", "qty"]
    size: float
    # risk_frac: fraction of NAV lost if stop is hit (stop required)
    # nav_frac:  fraction of NAV as position notional
    # target_weight: signed portfolio weight
    # qty: absolute units/contracts
    stop: float | None = None                  # price level
    take: float | None = None                  # price level
    time_stop_bars: int | None = None
    tag: str = ""                              # e.g. episode id


Signals = pd.DataFrame | list[OrderIntent]


@dataclass(frozen=True)
class StrategyMeta:
    key: str
    name: str
    doc_path: str
    output: str
    freq: str
    default_universe: str
    params: tuple[Param, ...]
    data_requirements: tuple[str, ...]
    data_required: bool                        # True => needs user-supplied CSV data
    group: str                                 # "A" moex-native | "B" csv-fed | "C" data-gated
    description: str


class Strategy(ABC):
    """Base class. Subclasses set the ClassVars and implement generate()."""

    key: ClassVar[str]
    name: ClassVar[str]
    doc_path: ClassVar[str]                    # strategies/<cat>/<doc>.md in this repo
    output: ClassVar[Literal["weights", "orders"]] = "weights"
    freq: ClassVar[Freq] = Freq.D1
    default_universe: ClassVar[str] = "moex_liquid"
    params: ClassVar[tuple[Param, ...]] = ()
    required_fields: ClassVar[frozenset[str]] = frozenset({"close", "total_return"})
    #: names from qbt.data.schemas.EVENT_SCHEMAS this strategy needs in ctx.events
    data_requirements: ClassVar[tuple[str, ...]] = ()
    #: "A" runs on MOEX data out of the box; "B" needs CSV events (fixture
    #: generators make it run green); "C" parameterized but data-gated.
    group: ClassVar[Literal["A", "B", "C"]] = "A"
    description: ClassVar[str] = ""

    def __init__(self, **kwargs: Any):
        spec = {p.name: p for p in self.params}
        unknown = set(kwargs) - set(spec)
        if unknown:
            raise ValueError(f"{self.key}: unknown params {sorted(unknown)}; known: {sorted(spec)}")
        self.p: dict[str, Any] = {}
        for name, param in spec.items():
            v = kwargs.get(name, param.default)
            if param.choices is not None and v not in param.choices:
                raise ValueError(f"{self.key}.{name}={v!r} not in {param.choices}")
            if param.low is not None and v is not None and v < param.low:
                raise ValueError(f"{self.key}.{name}={v} below allowed range [{param.low}, {param.high}]")
            if param.high is not None and v is not None and v > param.high:
                raise ValueError(f"{self.key}.{name}={v} above allowed range [{param.low}, {param.high}]")
            self.p[name] = v

    @abstractmethod
    def generate(self, ctx: DataContext) -> Signals: ...

    @classmethod
    def describe(cls) -> StrategyMeta:
        return StrategyMeta(
            key=cls.key, name=cls.name, doc_path=cls.doc_path, output=cls.output,
            freq=str(cls.freq), default_universe=cls.default_universe, params=cls.params,
            data_requirements=cls.data_requirements,
            data_required=cls.group != "A", group=cls.group, description=cls.description,
        )

    def check_data(self, ctx: DataContext) -> list[str]:
        """Return list of missing event tables (empty = ok)."""
        return [s for s in self.data_requirements if s not in ctx.events]


@runtime_checkable
class Overlay(Protocol):
    """Transforms a weights matrix post-generation, pre-execution-lag.

    Applied by the runner via `overlay=` option. Order strategies are not
    wrapped; the runner must warn when an overlay is requested on one, and when
    wrapping deliberately counter-cyclical strategies (e.g. index_panic_reversion
    declares compatible_overlays=()).
    """

    name: str

    def transform(self, weights: pd.DataFrame, ctx: DataContext) -> pd.DataFrame: ...
