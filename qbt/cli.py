"""qbt CLI (WS-E). Entry point: `qbt` (pyproject scripts)."""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(no_args_is_help=True, add_completion=False)
data_app = typer.Typer(no_args_is_help=True)
dev_app = typer.Typer(no_args_is_help=True)
app.add_typer(data_app, name="data")
app.add_typer(dev_app, name="dev")
console = Console()
_REPO = Path(__file__).resolve().parents[1]


def _parse_params(params: list[str]) -> dict:
    out = {}
    for p in params:
        k, _, v = p.partition("=")
        if v.lower() in ("true", "false"):
            out[k] = v.lower() == "true"
        else:
            try:
                out[k] = int(v) if re.fullmatch(r"-?\d+", v) else float(v)
            except ValueError:
                out[k] = v
    return out


@app.command()
def serve(host: str = "127.0.0.1", port: int = 8000, fake: bool = False):
    """Start the web terminal (single worker, no reload — see qbt/api/jobs.py)."""
    import uvicorn
    from qbt.api.app import create_app
    console.print(f"[bold cyan]qbt terminal[/] on http://{host}:{port}  "
                  f"(engine: {'fake' if fake else 'real'})")
    uvicorn.run(create_app(runner="fake" if fake else "real"),
                host=host, port=port, workers=1)


@app.command()
def run(strategy: str,
        param: list[str] = typer.Option([], "--param", "-p", help="k=v (repeatable)"),
        universe: str = typer.Option(None), start: str = "2018-01-01", end: str = "2025-12-31",
        cost_preset: str = "moex_equity", lag: int = 1, fake: bool = False,
        out: Path = typer.Option(None, help="save result dir")):
    """Run one backtest and print the metrics table."""
    from qbt.api.schemas import RunRequest
    from qbt.strategy import registry
    cls = registry.get(strategy)
    req = RunRequest(strategy_key=strategy, params=_parse_params(param),
                     universe=universe or cls.default_universe, start=start, end=end,
                     cost_preset=cost_preset, execution_lag=lag)
    if fake:
        from qbt.api.fake import FakeRunner
        res = FakeRunner().run(req, "cli")
    else:
        from qbt.api.real import RealRunner
        res = RealRunner().run(req, "cli")
    t = Table(title=f"{strategy}  {start}..{end}  ({'fake' if fake else 'real'})")
    t.add_column("metric"); t.add_column("value", justify="right")
    for k, v in res.metrics.items():
        t.add_row(k, f"{v:,.4f}" if isinstance(v, float) else str(v))
    console.print(t)
    if out:
        res.save(out)
        console.print(f"saved -> {out}")


@app.command()
def sweep(strategy: str,
          param: list[str] = typer.Option([], "--param", "-p",
                                          help="grid: name=lo:hi:step (repeatable) or fixed k=v"),
          universe: str = typer.Option(None), start: str = "2018-01-01", end: str = "2025-12-31",
          fake: bool = False):
    """Parameter sweep; prints top rows by Sharpe."""
    from qbt.api.schemas import SweepRequest
    from qbt.strategy import registry
    cls = registry.get(strategy)
    grid, fixed = {}, {}
    for p in param:
        k, _, v = p.partition("=")
        if ":" in v:
            lo, hi, *rest = v.split(":")
            step = float(rest[0]) if rest else 1.0
            vals, x = [], float(lo)
            while x <= float(hi) + 1e-12:
                vals.append(round(x, 10)); x += step
            grid[k] = vals
        else:
            fixed.update(_parse_params([p]))
    req = SweepRequest(strategy_key=strategy, params=fixed, grid=grid,
                       universe=universe or cls.default_universe, start=start, end=end)
    if fake:
        from qbt.api.fake import FakeRunner
        df = FakeRunner().sweep(req, "cli")
    else:
        from qbt.api.real import RealRunner
        df = RealRunner().sweep(req, "cli")
    df = df.sort_values("sharpe", ascending=False, na_position="last")
    t = Table(title=f"sweep {strategy} — top 15 by sharpe")
    for c in df.columns:
        t.add_column(str(c), justify="right")
    for _, r in df.head(15).iterrows():
        t.add_row(*[f"{v:.3f}" if isinstance(v, float) else str(v) for v in r])
    console.print(t)


@app.command("new-strategy")
def new_strategy(name: str):
    """Scaffold qbt/strategies/<name>.py from the template."""
    if not re.fullmatch(r"[a-z][a-z0-9_]+", name):
        raise typer.BadParameter("snake_case name required")
    dst = _REPO / "qbt" / "strategies" / f"{name}.py"
    if dst.exists():
        raise typer.BadParameter(f"{dst} already exists")
    src = _REPO / "qbt" / "strategy" / "_template.py"
    cls = "".join(w.capitalize() for w in name.split("_"))
    text = src.read_text().replace("MyStrategy", cls).replace('"my_strategy"', f'"{name}"') \
        .replace("My Strategy", cls)
    dst.write_text(text)
    console.print(f"created [bold]{dst}[/] (key: {name}). Edit params/doc_path, then it "
                  f"auto-registers; test with: pytest tests/strategies -k {name}")


@data_app.command("ensure")
def data_ensure(universe: str = "moex_liquid", start: str = "2015-01-01",
                end: str = typer.Option(None), freq: str = "1d", provider: str = "moex_iss"):
    """Pull missing history into the local cache."""
    from qbt.api.real import RealRunner
    from qbt.api.schemas import DataEnsureRequest
    req = DataEnsureRequest(universe=universe, start=start, end=end, freq=freq, provider=provider)
    with console.status(f"ensuring {universe} via {provider}…"):
        out = RealRunner().ensure(req, progress_cb=lambda p: None)
    console.print(json.dumps(out, indent=2, default=str))


@data_app.command("status")
def data_status():
    from qbt.api.real import RealRunner
    rows = RealRunner().data_status()
    t = Table(title="cache coverage")
    for c in ("symbol", "freq", "first_ts", "last_ts", "rows"):
        t.add_column(c)
    for r in rows[:300]:
        t.add_row(str(r.get("symbol")), str(r.get("freq")), str(r.get("first_ts"))[:10],
                  str(r.get("last_ts"))[:10], str(r.get("rows")))
    console.print(t)


@data_app.command("health")
def data_health():
    from qbt.api.real import RealRunner
    for h in RealRunner().data_health():
        mark = "[green]ok[/]" if h["ok"] else f"[red]{h['detail']}[/]"
        console.print(f"{h['provider']:10s} {mark}")


@dev_app.command("record-fixtures")
def record_fixtures(provider: str = "moex_iss"):
    """Record provider HTTP cassettes (run on a machine with keys for finam/algopack)."""
    import subprocess, sys
    script = _REPO / "scripts" / "record_fixtures.py"
    raise SystemExit(subprocess.call([sys.executable, str(script), "--provider", provider]))


if __name__ == "__main__":
    app()
