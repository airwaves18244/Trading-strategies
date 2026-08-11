"""BacktestResult + run JSON web contract. PHASE 0 CONTRACT (fully implemented).

Normalization rule (weights vs orders engines): BOTH engines must fill every
field below. For order strategies, `weights` is the realized position notional /
NAV (so exposure/turnover are comparable across engines).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

#: trades ledger columns (order engine fills all; weight engine fills through cost_bps)
TRADES_COLUMNS = (
    "ts", "symbol", "side", "qty", "price", "notional", "cost_bps", "reason", "tag", "pnl"
)
#: cost breakdown columns, per day
COST_COLUMNS = ("commission", "spread", "impact", "borrow")
#: exposure columns, per day
EXPOSURE_COLUMNS = ("gross", "net", "long", "short", "n_positions")


@dataclass
class RunMeta:
    run_id: str
    strategy_key: str
    params: dict[str, Any]
    universe: str
    start: str
    end: str
    freq: str
    cost_preset: str
    execution_lag: int
    overlay: str | None
    created_at: str
    engine: str = ""            # "weights" | "orders"
    notes: str = ""


@dataclass
class BacktestResult:
    equity: pd.Series                   # NAV, starts at 1.0
    returns_gross: pd.Series
    returns_net: pd.Series
    weights: pd.DataFrame               # target/realized weights (see normalization rule)
    positions: pd.DataFrame             # realized position notional / NAV
    trades: pd.DataFrame                # TRADES_COLUMNS
    costs: pd.DataFrame                 # COST_COLUMNS, per day, as return drag (fractions)
    exposure: pd.DataFrame              # EXPOSURE_COLUMNS
    metrics: dict[str, float]
    per_year: pd.DataFrame              # year, gross, net, cost_drag, sharpe_net, max_dd, n_trades
    meta: RunMeta
    benchmark_equity: pd.Series | None = None    # aligned to equity index (e.g. IMOEX TR)

    # ---------------- persistence ----------------

    def save(self, path: Path) -> None:
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        frames = {
            "equity": self.equity.to_frame("equity"),
            "returns_gross": self.returns_gross.to_frame("r"),
            "returns_net": self.returns_net.to_frame("r"),
            "weights": self.weights, "positions": self.positions,
            "trades": self.trades, "costs": self.costs, "exposure": self.exposure,
            "per_year": self.per_year,
        }
        if self.benchmark_equity is not None:
            frames["benchmark_equity"] = self.benchmark_equity.to_frame("equity")
        for name, df in frames.items():
            df.to_parquet(path / f"{name}.parquet")
        (path / "meta.json").write_text(json.dumps(
            {"meta": self.meta.__dict__, "metrics": self.metrics,
             # the parquet round-trip renames the series to "equity"; keep the
             # benchmark's symbol so benchmark_stats.symbol survives a reload
             "benchmark_symbol": (self.benchmark_equity.name or None)
             if self.benchmark_equity is not None else None},
            indent=2, default=str))

    @classmethod
    def load(cls, path: Path) -> "BacktestResult":
        path = Path(path)
        blob = json.loads((path / "meta.json").read_text())

        def rd(name: str) -> pd.DataFrame:
            return pd.read_parquet(path / f"{name}.parquet")

        bench_p = path / "benchmark_equity.parquet"
        return cls(
            equity=rd("equity")["equity"],
            returns_gross=rd("returns_gross")["r"],
            returns_net=rd("returns_net")["r"],
            weights=rd("weights"), positions=rd("positions"), trades=rd("trades"),
            costs=rd("costs"), exposure=rd("exposure"), per_year=rd("per_year"),
            metrics=blob["metrics"], meta=RunMeta(**blob["meta"]),
            benchmark_equity=pd.read_parquet(bench_p)["equity"].rename(blob.get("benchmark_symbol"))
            if bench_p.exists() else None,
        )

    # ---------------- web contract ----------------

    def to_run_json(self, max_points: int = 3000) -> dict[str, Any]:
        """The JSON the web terminal renders (run.json v2). Downsamples long series.

        v1 keys are byte-compatible; the v2 blocks are appended by
        analytics.report.extend_run_json so both runners get them for free.
        """
        from qbt.analytics.report import extend_run_json

        def ser(s: pd.Series) -> list[dict[str, Any]]:
            if len(s) > max_points:
                idx = np.linspace(0, len(s) - 1, max_points).astype(int)
                s = s.iloc[idx]
            return [{"time": int(pd.Timestamp(t).timestamp()), "value": None if pd.isna(v) else float(v)}
                    for t, v in s.items()]

        eq = self.equity.dropna()
        dd = eq / eq.cummax() - 1.0
        out: dict[str, Any] = {
            "meta": self.meta.__dict__,
            "metrics": {k: (None if v is None or (isinstance(v, float) and not np.isfinite(v)) else v)
                        for k, v in self.metrics.items()},
            "equity": ser(eq),
            "equity_gross": ser((1 + self.returns_gross.fillna(0)).cumprod()),
            "drawdown": ser(dd),
            "benchmark": ser(self.benchmark_equity.dropna()) if self.benchmark_equity is not None else None,
            "exposure": {c: ser(self.exposure[c]) for c in self.exposure.columns},
            "per_year": json.loads(self.per_year.to_json(orient="records")),
            "costs_total": {c: float(self.costs[c].sum()) for c in self.costs.columns},
            "trades": json.loads(
                self.trades.assign(ts=self.trades["ts"].astype(str)).to_json(orient="records")
            ) if len(self.trades) else [],
            "n_trades": int(len(self.trades)),
        }
        return extend_run_json(self, out)
