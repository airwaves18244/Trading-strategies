"""RealRunner — same interface as FakeRunner, wired to the actual data layer + engine.

Context assembly for a run:
  universe yaml -> symbols -> ParquetBarStore (cache) -> DataContext via
  DataService.load_context, dividends from cached corporate_actions, events from
  data/events/<schema>.csv when present. If the cache has no bars for the
  universe, raises a readable error telling the user to run `qbt data ensure`.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import pandas as pd
import yaml

from qbt.core.config import get_settings
from qbt.core.errors import DataGapError
from qbt.core.types import AssetClass, Freq, Instrument
from qbt.data.schemas import EVENT_SCHEMAS, validate_events
from qbt.engine.result import BacktestResult
from qbt.strategy import registry
from qbt.strategy.lib import VolTargetOverlay

_UNIVERSE_DIR = Path(__file__).resolve().parents[2] / "configs" / "universes"
_EVENTS_DIRNAME = "events"          # <repo>/data/events/<schema>.csv


def load_universe_config(name: str) -> dict[str, Any]:
    path = _UNIVERSE_DIR / f"{name}.yaml"
    if not path.exists():
        raise DataGapError(f"Unknown universe '{name}'. Available: "
                           f"{sorted(p.stem for p in _UNIVERSE_DIR.glob('*.yaml'))}")
    return yaml.safe_load(path.read_text()) or {}


_SECTOR_FILE = Path(__file__).resolve().parents[2] / "configs" / "instruments" / "moex_sectors.yaml"


def load_sectors() -> dict[str, str]:
    """Symbol -> sector. Sector-neutral and industry strategies are inert without it."""
    if not _SECTOR_FILE.exists():
        return {}
    return yaml.safe_load(_SECTOR_FILE.read_text()) or {}


def _instruments_for(symbols: list[str], futures: bool) -> dict[str, Instrument]:
    sectors = load_sectors()
    out = {}
    for s in symbols:
        ac = AssetClass.FUTURE if futures else (
            AssetClass.CRYPTO if s.startswith("CRYPTO:") else AssetClass.EQUITY)
        out[s] = Instrument(symbol=s, exchange=s.split(":")[0], asset_class=ac,
                            sector=sectors.get(s), lot_size=1,
                            provider_symbols={"moex_iss": s.split(":")[-1]})
    return out


def _load_events(repo_root: Path) -> dict[str, pd.DataFrame]:
    events: dict[str, pd.DataFrame] = {}
    ev_dir = repo_root / "data" / _EVENTS_DIRNAME
    if not ev_dir.exists():
        return events
    for f in ev_dir.glob("*.csv"):
        if f.stem in EVENT_SCHEMAS:
            try:
                events[f.stem] = validate_events(pd.read_csv(f), f.stem)
            except Exception as e:  # noqa: BLE001 - surface as warning, not crash
                import logging
                logging.getLogger("qbt.real").warning("Skipping %s: %s", f, e)
    return events


class RealRunner:
    name = "real"

    def __init__(self) -> None:
        self.settings = get_settings()
        self._repo_root = Path(__file__).resolve().parents[2]

    # ---------------- context ----------------

    def build_context(self, req: Any):
        from qbt.core.calendar import trading_days
        from qbt.data.manifest import Manifest
        from qbt.data.service import DataService
        from qbt.data.store import ParquetBarStore

        cfg = load_universe_config(req.universe)
        symbols = list(cfg.get("symbols", []))
        futures = bool(cfg.get("futures", False))
        cache = Path(self.settings.cache_dir)
        store = ParquetBarStore(cache / "bars")
        manifest = Manifest(cache / "manifest.sqlite")
        service = DataService(store=store, manifest=manifest, providers={},
                              calendar_fn=lambda s, e: trading_days(
                                  s, e, market="forts" if futures else "stock"))
        start = pd.Timestamp(req.start, tz="UTC")
        end = pd.Timestamp(req.end, tz="UTC")
        covered = [s for s in symbols if store.coverage(s, Freq(req.freq)) is not None]
        if not covered:
            raise DataGapError(
                f"No cached bars for universe '{req.universe}' ({req.freq}). "
                f"Run: qbt data ensure --universe {req.universe} --start {req.start}"
            )
        # Benchmark: an actual index, not covered[0] — comparing a total-return
        # strategy against the first universe member is meaningless. MCFTR is the
        # dividend-reinvested MOEX index, the like-for-like yardstick.
        bench = cfg.get("benchmark", "MOEX:MCFTR")
        if bench and store.coverage(bench, Freq(req.freq)) is not None and bench not in covered:
            covered = covered + [bench]
        elif bench and store.coverage(bench, Freq(req.freq)) is None:
            bench = covered[0] if covered else None

        instruments = _instruments_for(covered, futures)
        actions = service.load_corporate_actions(covered) if hasattr(service, "load_corporate_actions") else []
        ctx = service.load_context(
            symbols=covered, freq=Freq(req.freq), start=start.to_pydatetime(),
            end=end.to_pydatetime(), instruments=instruments,
            actions=actions, benchmark_symbol=bench,
            delisting_return_pct=self.settings.delisting_return_pct,
        )
        # the benchmark is a yardstick, not tradable inventory
        if bench and bench not in symbols and bench in ctx.universe_mask.columns:
            ctx.universe_mask[bench] = False
        ctx.events.update(_load_events(self._repo_root))
        return ctx

    # ---------------- runner interface (mirrors FakeRunner) ----------------

    def run(self, req: Any, run_id: str,
            progress_cb: Callable[[float], None] | None = None) -> BacktestResult:
        from qbt.engine.cost_models import load_cost_preset
        from qbt.engine.runner import run_backtest

        if progress_cb:
            progress_cb(0.05)
        strategy_cls = registry.get(req.strategy_key)
        params = dict(req.params or {})
        if req.long_only is not None and any(p.name == "long_only" for p in strategy_cls.params):
            params.setdefault("long_only", req.long_only)
        strategy = strategy_cls(**params)
        ctx = self.build_context(req)
        if progress_cb:
            progress_cb(0.35)
        overlay = VolTargetOverlay(target=req.vol_target) if req.overlay == "vol_target" \
            and req.vol_target else (VolTargetOverlay() if req.overlay == "vol_target" else None)
        res = run_backtest(
            strategy, ctx, cost_model=load_cost_preset(req.cost_preset),
            lag=req.execution_lag, overlay=overlay,
            initial_nav=1.0, cost_preset_name=req.cost_preset, run_id=run_id,
        )
        if progress_cb:
            progress_cb(0.95)
        return res

    def sweep(self, req: Any, run_id: str,
              progress_cb: Callable[[float], None] | None = None) -> pd.DataFrame:
        from qbt.engine.cost_models import load_cost_preset
        from qbt.engine.sweep import sweep as run_sweep

        strategy_cls = registry.get(req.strategy_key)
        ctx = self.build_context(req)
        return run_sweep(strategy_cls, dict(req.params or {}), req.grid, ctx,
                         cost_model=load_cost_preset(req.cost_preset),
                         progress_cb=progress_cb, lag=req.execution_lag)

    # ---------------- data ops ----------------

    def data_status(self) -> list[dict[str, Any]]:
        from qbt.data.manifest import Manifest
        cache = Path(self.settings.cache_dir)
        if not (cache / "manifest.sqlite").exists():
            return []
        return [
            {"symbol": c.symbol, "freq": str(c.freq), "first_ts": str(c.first_ts),
             "last_ts": str(c.last_ts), "rows": c.rows, "updated_at": str(c.updated_at)}
            for c in Manifest(cache / "manifest.sqlite").all_coverage()
        ]

    def data_health(self) -> list[dict[str, Any]]:
        from qbt.data.providers import make_provider
        out = []
        for name in ("moex_iss", "algopack", "finam"):
            try:
                h = make_provider(name, self.settings).health()
                out.append({"provider": name, "ok": h.ok, "detail": h.detail})
            except Exception as e:  # noqa: BLE001
                out.append({"provider": name, "ok": False, "detail": f"{type(e).__name__}: {e}"})
        return out

    def ensure(self, req: Any, progress_cb: Callable[[float], None] | None = None) -> dict[str, Any]:
        from qbt.core.calendar import trading_days
        from qbt.data.manifest import Manifest
        from qbt.data.providers import make_provider
        from qbt.data.service import DataService
        from qbt.data.store import ParquetBarStore

        cfg = load_universe_config(req.universe) if req.universe else {}
        symbols = req.symbols or list(cfg.get("symbols", []))
        futures = bool(cfg.get("futures", False))
        cache = Path(self.settings.cache_dir)
        provider = make_provider(req.provider, self.settings)
        service = DataService(
            store=ParquetBarStore(cache / "bars"), manifest=Manifest(cache / "manifest.sqlite"),
            providers={req.provider: provider},
            calendar_fn=lambda s, e: trading_days(s, e, market="forts" if futures else "stock"),
        )
        end = req.end or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        # DataService reports (done, total); the job registry wants a 0..1 fraction.
        cb = None if progress_cb is None else (
            lambda done, total: progress_cb(done / total if total else 1.0))
        service.ensure(symbols, Freq(req.freq),
                       pd.Timestamp(req.start, tz="UTC").to_pydatetime(),
                       pd.Timestamp(end, tz="UTC").to_pydatetime(),
                       req.provider, progress_cb=cb)
        cov = [c for c in self.data_status() if c.get("symbol") in set(symbols)]
        return {"symbols": symbols, "provider": req.provider, "coverage": cov}

    def bars(self, symbol: str, freq: str, start: str, end: str) -> list[dict[str, Any]]:
        from qbt.core.types import BarRequest
        from qbt.data.store import ParquetBarStore
        store = ParquetBarStore(Path(self.settings.cache_dir) / "bars")
        bf = store.read(BarRequest(symbols=[symbol], freq=Freq(freq),
                                   start=pd.Timestamp(start, tz="UTC").to_pydatetime(),
                                   end=pd.Timestamp(end, tz="UTC").to_pydatetime()))
        return [
            {"time": int(pd.Timestamp(r.ts).timestamp()), "open": r.open, "high": r.high,
             "low": r.low, "close": r.close, "volume": r.volume}
            for r in bf.df.itertuples()
        ]
