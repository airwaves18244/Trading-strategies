"""MOEX ISS provider (free, no API key).

Base: https://iss.moex.com/iss

Endpoints used:
  - daily equities:  /history/engines/stock/markets/shares/boards/TQBR/securities/<SECID>.json
  - daily futures:   /history/engines/futures/markets/forts/securities/<SECID>.json
  - daily indices:   /history/engines/stock/markets/index/securities/<SECID>.json
  - intraday:        /engines/stock/markets/shares/securities/<SECID>/candles.json?interval=1|10|60
  - PIT membership:  /history/engines/stock/markets/shares/boards/TQBR/securities.json?date=YYYY-MM-DD
  - dividends:       /securities/<SECID>/dividends.json
  - futures chains:  /statistics/engines/futures/markets/forts/series.json?asset_code=<code>&show_expired=1
  - index weights:   /statistics/engines/stock/markets/index/analytics/<INDEX>.json?date=...&limit=100

All ISS JSON payloads share one shape per named block:
    {"<block>": {"columns": [...], "data": [[...], ...]}, "<block>.cursor": {...}, ...}
`_parse_iss_block` is the single place that turns one of those blocks into a DataFrame.
"""
from __future__ import annotations

import re
import time
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

import pandas as pd
import requests

from qbt.core.errors import ProviderError, RateLimitError
from qbt.core.types import (
    AssetClass,
    BAR_SCHEMA,
    BarFrame,
    BarRequest,
    CorporateAction,
    Freq,
    FuturesContract,
    Instrument,
)
from qbt.data.interfaces import ProviderCapabilities, ProviderHealth

ISS_BASE = "https://iss.moex.com/iss"
USER_AGENT = "qbt/0.1"
PAGE_SIZE = 100
REQUEST_TIMEOUT = 30.0
MSK = ZoneInfo("Europe/Moscow")

#: Regular MOEX single-contract futures secid: 2-letter root + month code + 1-digit year,
#: e.g. "RIH5". Calendar-spread instruments ("RIH5RIM5", len 8) do NOT match and must be
#: dropped when building futures chains (architecture.md WS-B row).
_FUTURES_SECID_RE = re.compile(r"^[A-Z]{2}[FGHJKMNQUVXZ][0-9]$")

#: Small set of index secids we know how to route to the index history endpoint. Extend as
#: needed; anything not in this set and not matching _FUTURES_SECID_RE is treated as an
#: equity/TQBR instrument.
KNOWN_INDEX_SECIDS = frozenset({
    "IMOEX", "IMOEX2", "RTSI", "MOEXBC", "MOEXBMI", "MOEXOG", "MOEXEU", "MOEXTL",
    "MOEXCN", "MOEXFN", "MOEXMM", "MOEXCH", "MOEXTN", "MOEXRE", "MOEX10", "RGBITR",
})

_INTERVAL_BY_FREQ: dict[Freq, int] = {Freq.M1: 1, Freq.M10: 10, Freq.H1: 60}


def classify_secid(secid: str) -> AssetClass:
    """Best-effort routing of a bare SECID to the ISS endpoint family it lives under."""
    if secid in KNOWN_INDEX_SECIDS:
        return AssetClass.INDEX
    if _FUTURES_SECID_RE.match(secid):
        return AssetClass.FUTURE
    return AssetClass.EQUITY


def _strip_prefix(symbol: str) -> str:
    """'MOEX:SBER' -> 'SBER'; bare secids pass through unchanged."""
    return symbol.split(":", 1)[1] if ":" in symbol else symbol


def _parse_iss_block(payload: dict, block: str) -> pd.DataFrame:
    """Shared parser for ISS's {'block': {'columns': [...], 'data': [[...]]}} shape."""
    section = payload.get(block)
    if not section:
        return pd.DataFrame()
    return pd.DataFrame(section.get("data", []), columns=section.get("columns", []))


def _daily_ts(series: pd.Series) -> pd.Series:
    """Daily TRADEDATE strings -> UTC tz-aware midnight timestamps."""
    return pd.to_datetime(series, utc=True)


def _msk_to_utc(series: pd.Series) -> pd.Series:
    """Naive MSK datetime strings (as returned by the candles endpoint) -> UTC."""
    naive = pd.to_datetime(series)
    return naive.dt.tz_localize(MSK).dt.tz_convert("UTC")


class IssHttpClient:
    """Thin requests.Session wrapper: retry/backoff, 429 -> RateLimitError, 30s timeout."""

    def __init__(
        self,
        base_url: str = ISS_BASE,
        session: requests.Session | None = None,
        max_retries: int = 5,
        timeout: float = REQUEST_TIMEOUT,
    ):
        self.base_url = base_url.rstrip("/")
        self.session = session or requests.Session()
        self.session.headers.setdefault("User-Agent", USER_AGENT)
        self.max_retries = max_retries
        self.timeout = timeout

    def get_json(self, path: str, params: dict | None = None) -> dict:
        url = f"{self.base_url}{path}"
        backoff = 1.0
        last_exc: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                resp = self.session.get(url, params=params, timeout=self.timeout)
            except requests.RequestException as exc:
                last_exc = ProviderError(f"MOEX ISS request error: {exc}", provider="moex_iss")
                time.sleep(backoff)
                backoff *= 2
                continue
            if resp.status_code == 429:
                retry_after = float(resp.headers.get("Retry-After", backoff))
                if attempt == self.max_retries - 1:
                    raise RateLimitError(
                        "MOEX ISS rate limit exceeded", provider="moex_iss", retry_after=retry_after
                    )
                time.sleep(retry_after)
                backoff *= 2
                continue
            if resp.status_code >= 500:
                last_exc = ProviderError(
                    f"MOEX ISS server error {resp.status_code}", provider="moex_iss"
                )
                time.sleep(backoff)
                backoff *= 2
                continue
            if resp.status_code != 200:
                raise ProviderError(
                    f"MOEX ISS request failed: {resp.status_code} {resp.text[:200]}",
                    provider="moex_iss",
                )
            return resp.json()
        raise last_exc or ProviderError("MOEX ISS request failed after retries", provider="moex_iss")

    def get_paginated(self, path: str, params: dict, block: str, page_size: int = PAGE_SIZE) -> pd.DataFrame:
        """start=<row offset> cursor pagination, page_size rows/page (MOEX default: 100)."""
        frames: list[pd.DataFrame] = []
        start = 0
        while True:
            page_params = dict(params)
            page_params["start"] = start
            payload = self.get_json(path, page_params)
            df = _parse_iss_block(payload, block)
            if df.empty:
                break
            frames.append(df)
            if len(df) < page_size:
                break
            start += page_size
        if not frames:
            return pd.DataFrame()
        return pd.concat(frames, ignore_index=True)


class MoexIssProvider:
    """MarketDataProvider over MOEX ISS. Free, anonymous, no API key required."""

    name = "moex_iss"
    capabilities = ProviderCapabilities(
        freqs=frozenset({Freq.D1}),
        asset_classes=frozenset({AssetClass.EQUITY, AssetClass.FUTURE, AssetClass.INDEX}),
        max_history_days=None,
        pit_universe=True,
        corporate_actions=True,
        futures_chains=True,
        needs_key=False,
        rate_limit_per_min=None,  # ISS documents no hard anonymous quota; be polite anyway
    )

    def __init__(self, base_url: str = ISS_BASE, session: requests.Session | None = None):
        self._client = IssHttpClient(base_url=base_url, session=session)

    # -- bars -----------------------------------------------------------------

    def fetch_bars(self, req: BarRequest) -> BarFrame:
        frames: list[pd.DataFrame] = []
        for raw_symbol in req.symbols:
            secid = _strip_prefix(raw_symbol)
            if req.freq == Freq.D1:
                df = self._fetch_daily_bars(secid, req.start, req.end)
            elif req.freq in _INTERVAL_BY_FREQ:
                df = self._fetch_intraday_bars(secid, req.freq, req.start, req.end)
            else:
                raise ProviderError(
                    f"moex_iss does not support freq={req.freq!r}", provider="moex_iss"
                )
            if df.empty:
                continue
            df.insert(0, "symbol", raw_symbol)
            frames.append(df)
        if not frames:
            return BarFrame.empty_frame()
        out = pd.concat(frames, ignore_index=True)
        return BarFrame.validate(out)

    def _fetch_daily_bars(self, secid: str, start: datetime, end: datetime) -> pd.DataFrame:
        kind = classify_secid(secid)
        params = {"from": start.date().isoformat(), "till": end.date().isoformat()}
        if kind == AssetClass.FUTURE:
            path = f"/history/engines/futures/markets/forts/securities/{secid}.json"
            raw = self._client.get_paginated(path, params, "history")
            if raw.empty:
                return pd.DataFrame()
            close = raw["CLOSE"].where(raw["CLOSE"].notna(), raw["SETTLEPRICE"])
            out = pd.DataFrame({
                "ts": _daily_ts(raw["TRADEDATE"]),
                "open": raw["OPEN"],
                "high": raw["HIGH"],
                "low": raw["LOW"],
                "close": close,
                "volume": raw["VOLUME"],
                "value": raw["VALUE"],
                "oi": raw["OPENPOSITION"],
            })
        elif kind == AssetClass.INDEX:
            path = f"/history/engines/stock/markets/index/securities/{secid}.json"
            raw = self._client.get_paginated(path, params, "history")
            if raw.empty:
                return pd.DataFrame()
            out = pd.DataFrame({
                "ts": _daily_ts(raw["TRADEDATE"]),
                "open": raw["OPEN"],
                "high": raw["HIGH"],
                "low": raw["LOW"],
                "close": raw["CLOSE"],
                "volume": raw["VOLUME"],
                "value": raw["VALUE"],
                "oi": float("nan"),
            })
        else:
            path = f"/history/engines/stock/markets/shares/boards/TQBR/securities/{secid}.json"
            raw = self._client.get_paginated(path, params, "history")
            if raw.empty:
                return pd.DataFrame()
            out = pd.DataFrame({
                "ts": _daily_ts(raw["TRADEDATE"]),
                "open": raw["OPEN"],
                "high": raw["HIGH"],
                "low": raw["LOW"],
                "close": raw["CLOSE"],
                "volume": raw["VOLUME"],
                "value": raw["VALUE"],
                "oi": float("nan"),
            })
        return out

    def _fetch_intraday_bars(self, secid: str, freq: Freq, start: datetime, end: datetime) -> pd.DataFrame:
        interval = _INTERVAL_BY_FREQ[freq]
        path = f"/engines/stock/markets/shares/securities/{secid}/candles.json"
        params = {
            "interval": interval,
            "from": start.strftime("%Y-%m-%d %H:%M:%S"),
            "till": end.strftime("%Y-%m-%d %H:%M:%S"),
        }
        raw = self._client.get_paginated(path, params, "candles")
        if raw.empty:
            return pd.DataFrame()
        return pd.DataFrame({
            "ts": _msk_to_utc(raw["begin"]),
            "open": raw["open"],
            "high": raw["high"],
            "low": raw["low"],
            "close": raw["close"],
            "volume": raw["volume"],
            "value": raw["value"],
            "oi": float("nan"),
        })

    # -- instruments / PIT universe --------------------------------------------

    def list_instruments(
        self, asof: date | None = None, asset_class: AssetClass | None = None
    ) -> list[Instrument]:
        if asset_class is not None and asset_class != AssetClass.EQUITY:
            return []
        asof = asof or date.today()
        path = "/history/engines/stock/markets/shares/boards/TQBR/securities.json"
        raw = self._client.get_paginated(path, {"date": asof.isoformat()}, "history")
        if raw.empty:
            return []
        out: list[Instrument] = []
        for _, row in raw.drop_duplicates(subset=["SECID"]).iterrows():
            secid = row["SECID"]
            out.append(
                Instrument(
                    symbol=f"MOEX:{secid}",
                    exchange="MOEX",
                    asset_class=AssetClass.EQUITY,
                    currency=row.get("CURRENCYID") or "RUB",
                    board="TQBR",
                    provider_symbols={"moex_iss": secid},
                )
            )
        return out

    # -- corporate actions -------------------------------------------------

    def fetch_corporate_actions(self, symbol: str) -> list[CorporateAction]:
        secid = _strip_prefix(symbol)
        payload = self._client.get_json(f"/securities/{secid}/dividends.json")
        df = _parse_iss_block(payload, "dividends")
        if df.empty:
            return []
        out: list[CorporateAction] = []
        for _, row in df.iterrows():
            ex_date = pd.Timestamp(row["registryclosedate"]).date()
            out.append(
                CorporateAction(symbol=symbol, ex_date=ex_date, kind="div", value=float(row["value"]))
            )
        return out

    # -- futures chains ------------------------------------------------------

    def fetch_futures_chain(self, asset_code: str, include_expired: bool = True) -> list[FuturesContract]:
        path = "/statistics/engines/futures/markets/forts/series.json"
        params = {"asset_code": asset_code, "show_expired": 1}
        payload = self._client.get_json(path, params)
        df = _parse_iss_block(payload, "series")
        if df.empty:
            return []
        # Drop calendar-spread instruments (secid doesn't match single-contract pattern).
        df = df[df["secid"].astype(str).map(lambda s: bool(_FUTURES_SECID_RE.match(s)))]
        if not include_expired and "is_traded" in df.columns:
            df = df[df["is_traded"].astype(int) == 1]
        out: list[FuturesContract] = []
        for _, row in df.iterrows():
            out.append(
                FuturesContract(
                    symbol=f"MOEX:{row['secid']}",
                    asset_code=row.get("asset_code", asset_code),
                    start=pd.Timestamp(row["start_date"]).date(),
                    expiry=pd.Timestamp(row["expiration_date"]).date(),
                    point_value=1.0,
                )
            )
        return out

    # -- PIT index constituents (public helper; WS-A universe consumes the saved output) --

    def fetch_index_constituents(self, index: str = "IMOEX", date_: date | None = None) -> pd.DataFrame:
        """Point-in-time index weights. Returns DataFrame[date, symbol, weight]."""
        date_ = date_ or date.today()
        path = f"/statistics/engines/stock/markets/index/analytics/{index}.json"
        params = {"date": date_.isoformat(), "limit": PAGE_SIZE}
        raw = self._client.get_paginated(path, params, "analytics")
        if raw.empty:
            return pd.DataFrame(columns=["date", "symbol", "weight"])
        out = pd.DataFrame({
            "date": pd.to_datetime(raw["tradedate"]).dt.date,
            "symbol": "MOEX:" + raw["secids"].astype(str),
            "weight": pd.to_numeric(raw["weight"], errors="coerce"),
        })
        return out.reset_index(drop=True)

    # -- health ---------------------------------------------------------------

    def health(self) -> ProviderHealth:
        try:
            payload = self._client.get_json(
                "/history/engines/stock/markets/shares/boards/TQBR/securities/SBER.json",
                {"from": date.today().isoformat(), "till": date.today().isoformat()},
            )
        except ProviderError as exc:
            return ProviderHealth(ok=False, provider=self.name, detail=str(exc))
        ok = "history" in payload
        return ProviderHealth(ok=ok, provider=self.name, detail="sample SBER fetch ok" if ok else "unexpected payload")


__all__ = ["MoexIssProvider", "IssHttpClient", "classify_secid", "KNOWN_INDEX_SECIDS", "ISS_BASE"]
