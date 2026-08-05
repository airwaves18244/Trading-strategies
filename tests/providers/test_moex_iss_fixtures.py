"""MOEX ISS provider parsing against recorded cassettes (offline)."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "http" / "moex_iss"


def _fixture(name: str) -> dict:
    return json.loads((FIXTURES / f"{name}.json").read_text())


class _Resp:
    def __init__(self, blob):
        self._blob = blob
        self.status_code = blob.get("status", 200)
        self.headers = {"Content-Type": "application/json"}

    def json(self):
        body = self._blob["body"]
        return json.loads(body) if isinstance(body, str) else body

    @property
    def text(self):
        body = self._blob["body"]
        return body if isinstance(body, str) else json.dumps(body)

    def raise_for_status(self):
        pass


@pytest.fixture
def provider():
    from qbt.data.providers.moex_iss import MoexIssProvider
    return MoexIssProvider()


def _patch_get(blobs):
    """Patch session.get to serve recorded bodies in order/matching by substring."""
    def fake_get(url, *a, **kw):
        for frag, blob in blobs.items():
            if frag in str(url):
                return _Resp(blob)
        return _Resp({"status": 200, "body": {"history": {"columns": [], "data": []},
                                              "history.cursor": {"columns": ["INDEX", "TOTAL", "PAGESIZE"],
                                                                 "data": [[0, 0, 100]]}}})
    return fake_get


def test_daily_bars_parse(provider):
    blob = _fixture("sber_daily_2023")
    with patch.object(provider._client.session, "get", side_effect=_patch_get({"SBER": blob})):
        from qbt.core.types import BarRequest, Freq
        import pandas as pd
        req = BarRequest(symbols=["MOEX:SBER"], freq=Freq.D1,
                         start=pd.Timestamp("2023-01-01", tz="UTC").to_pydatetime(),
                         end=pd.Timestamp("2023-03-01", tz="UTC").to_pydatetime())
        bf = provider.fetch_bars(req)
    assert len(bf) > 10
    assert str(bf.df.ts.dt.tz) == "UTC"
    assert bf.df.ts.is_monotonic_increasing or bf.df.sort_values(["symbol", "ts"]).equals(bf.df)
    assert (bf.df.close > 0).all()


def test_futures_chain_filters_calendar_spreads(provider):
    blob = _fixture("rts_series_show_expired")
    with patch.object(provider._client.session, "get", side_effect=_patch_get({"series": blob})):
        chain = provider.fetch_futures_chain("RTS", include_expired=True)
    assert len(chain) > 20
    for c in chain:
        secid = c.symbol.split(":")[-1]
        assert len(secid) == 4, f"calendar spread leaked: {secid}"


def test_dividends_parse(provider):
    blob = _fixture("sber_dividends")
    with patch.object(provider._client.session, "get", side_effect=_patch_get({"dividends": blob})):
        actions = provider.fetch_corporate_actions("MOEX:SBER")
    assert len(actions) >= 5
    assert all(a.kind == "div" and a.value > 0 for a in actions)
