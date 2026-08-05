"""MOEX ALGOPACK provider (paid; needs a data.moex.com Bearer token).

Base: https://iss.moex.com/iss/datashop/algopack

Endpoints:
  - /eq/tradestats/<SECID>.json  5-min trade stats -> mapped to BarFrame
  - /eq/obstats/<SECID>.json     5-min orderbook stats -> fetch_obstats() DataFrame,
                                 used for spread/cost calibration (spread_bps estimate)

CRITICAL auth-failure mode: an invalid/missing token does NOT get a 401/403 — ALGOPACK
replies HTTP 200 with an HTML login page. We detect that via Content-Type: text/html or a
body starting with '<' and raise ProviderAuthError so callers don't silently parse garbage.

Field names for tradestats/obstats below are transcribed from MOEX's public ALGOPACK
documentation; they cannot be exercised against a live token from this sandbox (no key
available here). tests/providers/test_algopack.py exercises them against hand-written
fixtures in tests/fixtures/algopack/. Verify against a live response if the shape drifts.
"""
from __future__ import annotations

import time
from datetime import date, datetime
from zoneinfo import ZoneInfo

import pandas as pd
import requests

from qbt.core.errors import ProviderAuthError, ProviderError, RateLimitError
from qbt.core.types import (
    AssetClass, BarFrame, BarRequest, CorporateAction, Freq, FuturesContract, Instrument,
)
from qbt.data.interfaces import ProviderCapabilities, ProviderHealth

ALGOPACK_BASE = "https://iss.moex.com/iss/datashop/algopack"
USER_AGENT = "qbt/0.1"
REQUEST_TIMEOUT = 30.0
MSK = ZoneInfo("Europe/Moscow")


def _strip_prefix(symbol: str) -> str:
    return symbol.split(":", 1)[1] if ":" in symbol else symbol


def _parse_block(payload: dict, block: str) -> pd.DataFrame:
    section = payload.get(block)
    if not section:
        return pd.DataFrame()
    return pd.DataFrame(section.get("data", []), columns=section.get("columns", []))


def _ts_from_date_time(date_col: pd.Series, time_col: pd.Series) -> pd.Series:
    combined = date_col.astype(str) + " " + time_col.astype(str)
    naive = pd.to_datetime(combined)
    return naive.dt.tz_localize(MSK).dt.tz_convert("UTC")


class AlgopackAuthClient:
    """requests.Session wrapper with Bearer auth and the HTML-login-page auth-failure check."""

    def __init__(
        self,
        token: str,
        base_url: str = ALGOPACK_BASE,
        session: requests.Session | None = None,
        max_retries: int = 5,
        timeout: float = REQUEST_TIMEOUT,
    ):
        self.token = token
        self.base_url = base_url.rstrip("/")
        self.session = session or requests.Session()
        self.session.headers.setdefault("User-Agent", USER_AGENT)
        self.max_retries = max_retries
        self.timeout = timeout

    def get_json(self, path: str, params: dict | None = None) -> dict:
        url = f"{self.base_url}{path}"
        headers = {"Authorization": f"Bearer {self.token}"}
        backoff = 1.0
        last_exc: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                resp = self.session.get(url, params=params, headers=headers, timeout=self.timeout)
            except requests.RequestException as exc:
                last_exc = ProviderError(f"ALGOPACK request error: {exc}", provider="algopack")
                time.sleep(backoff)
                backoff *= 2
                continue
            if resp.status_code == 429:
                if attempt == self.max_retries - 1:
                    raise RateLimitError("ALGOPACK rate limit exceeded", provider="algopack")
                time.sleep(float(resp.headers.get("Retry-After", backoff)))
                backoff *= 2
                continue
            if resp.status_code >= 500:
                last_exc = ProviderError(f"ALGOPACK server error {resp.status_code}", provider="algopack")
                time.sleep(backoff)
                backoff *= 2
                continue
            self._raise_if_html_login(resp)
            if resp.status_code != 200:
                raise ProviderError(
                    f"ALGOPACK request failed: {resp.status_code} {resp.text[:200]}", provider="algopack"
                )
            try:
                return resp.json()
            except ValueError as exc:
                raise ProviderAuthError(
                    f"ALGOPACK returned a non-JSON body (likely an auth problem): {resp.text[:200]}",
                    provider="algopack",
                ) from exc
        raise last_exc or ProviderError("ALGOPACK request failed after retries", provider="algopack")

    @staticmethod
    def _raise_if_html_login(resp: requests.Response) -> None:
        content_type = resp.headers.get("Content-Type", "")
        body = resp.text
        if "text/html" in content_type.lower() or body.lstrip().startswith("<"):
            raise ProviderAuthError(
                "ALGOPACK returned HTTP 200 with an HTML login page instead of JSON — the "
                "token is missing, invalid, or expired. Set QBT_ALGOPACK_TOKEN to a valid "
                "data.moex.com ALGOPACK subscription token.",
                provider="algopack",
            )


class AlgopackProvider:
    """MarketDataProvider over MOEX ALGOPACK (tradestats/obstats). Requires a Bearer token."""

    name = "algopack"
    capabilities = ProviderCapabilities(
        freqs=frozenset({Freq.M5}),
        asset_classes=frozenset({AssetClass.EQUITY}),
        max_history_days=None,
        pit_universe=False,
        corporate_actions=False,
        futures_chains=False,
        needs_key=True,
        rate_limit_per_min=None,
    )

    def __init__(self, token: str, base_url: str = ALGOPACK_BASE, session: requests.Session | None = None):
        if not token:
            raise ProviderAuthError("AlgopackProvider requires a non-empty token", provider="algopack")
        self._client = AlgopackAuthClient(token=token, base_url=base_url, session=session)

    # -- bars (tradestats) -----------------------------------------------------

    def fetch_bars(self, req: BarRequest) -> BarFrame:
        frames: list[pd.DataFrame] = []
        for raw_symbol in req.symbols:
            secid = _strip_prefix(raw_symbol)
            df = self._fetch_tradestats(secid, req.start, req.end)
            if df.empty:
                continue
            df.insert(0, "symbol", raw_symbol)
            frames.append(df)
        if not frames:
            return BarFrame.empty_frame()
        return BarFrame.validate(pd.concat(frames, ignore_index=True))

    def _fetch_tradestats(self, secid: str, start: datetime, end: datetime) -> pd.DataFrame:
        path = f"/eq/tradestats/{secid}.json"
        params = {"from": start.date().isoformat(), "till": end.date().isoformat()}
        payload = self._client.get_json(path, params)
        df = _parse_block(payload, "data")
        if df.empty:
            return pd.DataFrame()
        return pd.DataFrame({
            "ts": _ts_from_date_time(df["tradedate"], df["tradetime"]),
            "open": df["pr_open"],
            "high": df["pr_high"],
            "low": df["pr_low"],
            "close": df["pr_close"],
            "volume": df["vol"],
            "value": df["val"],
            "oi": float("nan"),
        })

    # -- obstats (spread calibration) ------------------------------------------

    def fetch_obstats(self, symbol: str, start: datetime, end: datetime) -> pd.DataFrame:
        """5-min orderbook stats incl. a spread_bps estimate, for cost-model calibration."""
        secid = _strip_prefix(symbol)
        path = f"/eq/obstats/{secid}.json"
        params = {"from": start.date().isoformat(), "till": end.date().isoformat()}
        payload = self._client.get_json(path, params)
        df = _parse_block(payload, "data")
        if df.empty:
            return pd.DataFrame(columns=["symbol", "ts", "spread_bbo", "spread_bps"])
        out = pd.DataFrame({
            "symbol": symbol,
            "ts": _ts_from_date_time(df["tradedate"], df["tradetime"]),
            "spread_bbo": pd.to_numeric(df.get("spread_bbo"), errors="coerce"),
            "spread_lv10": pd.to_numeric(df.get("spread_lv10"), errors="coerce") if "spread_lv10" in df else float("nan"),
            "levels_b": pd.to_numeric(df.get("levels_b"), errors="coerce") if "levels_b" in df else float("nan"),
            "levels_s": pd.to_numeric(df.get("levels_s"), errors="coerce") if "levels_s" in df else float("nan"),
        })
        # spread_bbo is documented as a relative (fractional) best-bid/offer spread;
        # spread_bps = spread_bbo * 10_000. Re-check against a live sample before relying
        # on this for production cost calibration.
        out["spread_bps"] = out["spread_bbo"] * 10_000
        return out

    # -- unsupported for ALGOPACK -----------------------------------------------

    def list_instruments(
        self, asof: date | None = None, asset_class: AssetClass | None = None
    ) -> list[Instrument]:
        raise ProviderError("ALGOPACK does not provide instrument listings; use moex_iss", provider="algopack")

    def fetch_corporate_actions(self, symbol: str) -> list[CorporateAction]:
        raise ProviderError("ALGOPACK does not provide corporate actions; use moex_iss", provider="algopack")

    def fetch_futures_chain(self, asset_code: str, include_expired: bool = True) -> list[FuturesContract]:
        raise ProviderError("ALGOPACK does not provide futures chains; use moex_iss", provider="algopack")

    # -- health -----------------------------------------------------------------

    def health(self) -> ProviderHealth:
        try:
            self._client.get_json("/eq/tradestats/SBER.json", {"from": date.today().isoformat(), "till": date.today().isoformat()})
        except ProviderAuthError as exc:
            return ProviderHealth(ok=False, provider=self.name, detail=str(exc))
        except ProviderError as exc:
            return ProviderHealth(ok=False, provider=self.name, detail=str(exc))
        return ProviderHealth(ok=True, provider=self.name, detail="token accepted")


__all__ = ["AlgopackProvider", "AlgopackAuthClient", "ALGOPACK_BASE"]
