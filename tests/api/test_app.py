"""API lifecycle tests against the FakeRunner."""
from __future__ import annotations

import threading
import time

import pytest
from fastapi.testclient import TestClient

from qbt.api.app import create_app
from qbt.api.jobs import JobRegistry


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


# ---------------- API v2 (docs/ui-upgrade.md section 2) ----------------


def _submit_run(client, **overrides):
    body = {"strategy_key": "ts_momentum", "start": "2020-01-01", "end": "2020-06-30"}
    body.update(overrides)
    r = client.post("/api/runs", json=body)
    assert r.status_code == 200, r.text
    rid = r.json()["run_id"]
    _wait(client, f"/api/runs/{rid}")
    return rid


def test_runs_listing_has_meta_and_summary(client):
    rid = _submit_run(client, params={"lookback": 20})
    rows = client.get("/api/runs").json()
    row = next(x for x in rows if x["run_id"] == rid)
    for key in ("strategy_key", "universe", "start", "end", "params", "label", "starred", "summary"):
        assert key in row, key
    assert row["params"] == {"lookback": 20}
    assert row["label"] == "" and row["starred"] is False
    assert set(row["summary"]) == {"sharpe", "cagr", "max_dd"}


def test_patch_label_and_star_persist_across_fresh_registry(client):
    rid = _submit_run(client)

    resp = client.patch(f"/api/runs/{rid}", json={"label": "my run", "starred": True})
    assert resp.status_code == 200
    body = resp.json()
    assert body["label"] == "my run" and body["starred"] is True

    # partial patch must not clobber the label already set above
    resp2 = client.patch(f"/api/runs/{rid}", json={"starred": False})
    assert resp2.status_code == 200
    assert resp2.json()["label"] == "my run" and resp2.json()["starred"] is False

    # simulate a process restart: a fresh JobRegistry re-scanning the same runs_dir
    fresh = JobRegistry(client.app.state.jobs.runs_dir)
    st = fresh.status(rid)
    assert st["label"] == "my run" and st["starred"] is False


def test_patch_unknown_run_404(client):
    assert client.patch("/api/runs/doesnotexist", json={"label": "x"}).status_code == 404


def test_delete_run(client):
    rid = _submit_run(client)
    resp = client.delete(f"/api/runs/{rid}")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}
    assert client.get(f"/api/runs/{rid}").status_code == 404
    assert not (client.app.state.jobs.runs_dir / rid).exists()


def test_delete_unknown_run_404(client):
    assert client.delete("/api/runs/doesnotexist").status_code == 404


def test_delete_running_job_409(client):
    ev = threading.Event()
    jobs = client.app.state.jobs
    rid = jobs.submit("run", lambda run_id, cb: ev.wait(2))
    try:
        for _ in range(100):
            if jobs.status(rid)["state"] in ("queued", "running"):
                break
            time.sleep(0.01)
        resp = client.delete(f"/api/runs/{rid}")
        assert resp.status_code == 409
    finally:
        ev.set()
        _wait(client, f"/api/runs/{rid}")
        jobs.delete(rid)  # cleanup now that it's done


def test_compare_happy_path(client):
    ids = [_submit_run(client, end="2020-03-31"), _submit_run(client, end="2020-06-30")]
    resp = client.get("/api/compare", params={"ids": ",".join(ids)})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["runs"]) == 2
    for run in body["runs"]:
        assert run["run_id"] in ids
        assert "meta" in run and "metrics" in run
        assert "sharpe" in run["metrics"]
        assert 0 < len(run["equity"]) <= 1500
        assert {"time", "value"} <= set(run["equity"][0])


def test_compare_bad_id_count_400(client):
    assert client.get("/api/compare", params={"ids": "onlyone"}).status_code == 400


def test_compare_missing_id_404(client):
    resp = client.get("/api/compare", params={"ids": "aaaaaaaaaaaa,bbbbbbbbbbbb"})
    assert resp.status_code == 404


def test_compare_rejects_non_done_run_400(client):
    ev = threading.Event()
    jobs = client.app.state.jobs
    running_id = jobs.submit("run", lambda run_id, cb: ev.wait(2))
    done_id = _submit_run(client)
    try:
        resp = client.get("/api/compare", params={"ids": f"{running_id},{done_id}"})
        assert resp.status_code == 400
    finally:
        ev.set()
        _wait(client, f"/api/runs/{running_id}")


def test_fake_sweep_has_is_oos_columns(client):
    r = client.post("/api/sweeps", json={
        "strategy_key": "ts_momentum", "start": "2020-01-01", "end": "2020-12-31",
        "grid": {"per_asset_target": [0.1, 0.2]}})
    rid = r.json()["run_id"]
    st = _wait(client, f"/api/sweeps/{rid}")
    assert len(st["rows"]) == 2
    for row in st["rows"]:
        assert "sharpe_is" in row and "sharpe_oos" in row
