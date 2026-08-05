"""API lifecycle tests against the FakeRunner."""
from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient

from qbt.api.app import create_app


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    app = create_app(runner="fake", runs_dir=tmp_path_factory.mktemp("runs"))
    return TestClient(app)


def _wait(client, url, tries=200):
    for _ in range(tries):
        st = client.get(url).json()
        if st["state"] in ("done", "error"):
            return st
        time.sleep(0.05)
    raise TimeoutError(url)


def test_index_serves_ui(client):
    html = client.get("/").text
    assert "chart-main" in html and "qbt" in html


def test_strategies_meta_shape(client):
    metas = client.get("/api/strategies").json()
    assert len(metas) == 43
    m = next(s for s in metas if s["key"] == "ts_momentum")
    assert m["params"] and {"name", "default", "low", "high"} <= set(m["params"][0])
    assert any(s["data_required"] for s in metas)          # group B/C flagged


def test_run_lifecycle_and_result_contract(client):
    r = client.post("/api/runs", json={"strategy_key": "ts_momentum",
                                       "start": "2020-01-01", "end": "2021-12-31"})
    assert r.status_code == 200
    rid = r.json()["run_id"]
    st = _wait(client, f"/api/runs/{rid}")
    assert st["state"] == "done", st
    res = client.get(f"/api/runs/{rid}/result").json()
    for key in ("equity", "equity_gross", "drawdown", "benchmark", "metrics",
                "per_year", "trades", "exposure", "costs_total"):
        assert key in res, key
    assert res["equity"][0]["time"] > 1e9                   # epoch seconds


def test_sweep_lifecycle(client):
    r = client.post("/api/sweeps", json={
        "strategy_key": "ts_momentum", "start": "2020-01-01", "end": "2020-12-31",
        "grid": {"per_asset_target": [0.1, 0.2]}})
    rid = r.json()["run_id"]
    st = _wait(client, f"/api/sweeps/{rid}")
    assert st["state"] == "done" and len(st["rows"]) == 2


def test_doc_extraction(client):
    d = client.get("/api/strategies/pairs_trading/doc").json()
    assert "Signal" in d["markdown"] or "signal" in d["markdown"]


def test_unknown_strategy_404(client):
    assert client.get("/api/strategies/nope/doc").status_code == 404
