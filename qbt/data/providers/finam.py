"""Finam Trade API provider (REST). Needs a user API secret exchanged for a JWT.

Live verification of this provider is impossible from this sandboxed container: outbound
network here is only reachable to iss.moex.com (see qbt/data/providers/moex_iss.py), not
api.finam.ru. Every endpoint path, timeframe token, and response-shape assumption below is
transcribed from the Finam TradeAPI v1 docs as given in the WS-B task brief and is isolated
as a module constant marked "VERIFY-ON-WINDOWS" — re-check each one against a live key on
the target Windows machine before relying on this provider for real runs.
tests/providers/test_finam.py exercises the JWT refresh/thread-safety logic and bar parsing
against hand-written fixtures (tests/fixtures/finam/), marked @pytest.mark.contract.
"""
from __future__ import annotations

import threading
import time
from datetime import date, datetime, timedelta, timezone

import pandas as pd
import requests

from qbt.core.errors import ProviderAuthError, ProviderError, RateLimitError
from qbt.core.types import (
    AssetClass, BarFrame, BarRequest, CorporateAction, Freq, FuturesContract, Instrument,
)
from qbt.data.interfaces import ProviderCapabilities, ProviderHealth

# --------------------------------------------------------------------------------------
# VERIFY-ON-WINDOWS: all Finam TradeAPI v1 endpoint paths / field names / enum tokens.
# --------------------------------------------------------------------------------------
FINAM_BASE_URL = "https://api.finam.ru"  # VERIFY-ON-WINDOWS
FINAM_AUTH_PATH = "/v1/sessions"  # VERIFY-ON-WINDOWS: POST {"secret": token} -> {"token": jwt}
FINAM_AUTH_TOKEN_FIELD = "token"  # VERIFY-ON-WINDOWS: key holding the JWT in the auth response
FINAM_BARS_PATH_TMPL = "/v1/instruments/{symbol}/bars"  # VERIFY-ON-WINDOWS
FINAM_BARS_TIMEFRAME_PARAM = "timeframe"  # VERIFY-ON-WINDOWS
FINAM_BARS_START_PARAM = "interval.start_time"  # VERIFY-ON-WINDOWS
FINAM_BARS_END_PARAM = "interval.end_time"  # VERIFY-ON-WINDOWS

# Timeframe enum tokens. VERIFY-ON-WINDOWS (esp. M10: Finam may not offer a native 10-minute
# bar; if so, ts=M10 requests must be resampled client-side from M1/M5 — not implemented here).
FINAM_TIMEFRAME_M1 = "TIME_FRAME_M1"  # VERIFY-ON-WINDOWS
FINAM_TIMEFRAME_M5 = "TIME_FRAME_M5"  # VERIFY-ON-WINDOWS
FINAM_TIMEFRAME_H1 = "TIME_FRAME_H1"  # VERIFY-ON-WINDOWS
FINAM_TIMEFRAME_D1 = "TIME_FRAME_D"  # VERIFY-ON-WINDOWS

_TIMEFRAME_BY_FREQ: dict[Freq, str] = {
    Freq.M1: FINAM_TIMEFRAME_M1,
    Freq.M5: FINAM_TIMEFRAME_M5,
    Freq.H1: FINAM_TIMEFRAME_H1,
    Freq.D1: FINAM_TIMEFRAME_D1,
}

# Response shape assumptions (VERIFY-ON-WINDOWS): auth returns {"token": "<jwt>"} (no
# expiry field documented -> we track the 15-min lifetime ourselves); bars endpoint returns
# {"bars": [{"timestamp": "...", "open": "...", "high": "...", "low": "...",
#            "close": "...", "volume": "..."}, ...]} with numeric fields as strings.
FINAM_BARS_RESPONSE_KEY = "bars"  # VERIFY-ON-WINDOWS

# Symbol suffixes. VERIFY-ON-WINDOWS: "@MISX" (MOEX main board) is documented for equities;
# the futures (FORTS) suffix is an unverified guess pending confirmation.
FINAM_EQUITY_SUFFIX = "@MISX"  # VERIFY-ON-WINDOWS
FINAM_FUTURE_SUFFIX = "@RTSX"  # VERIFY-ON-WINDOWS: guess for FORTS-listed futures

JWT_LIFETIME_SECONDS = 15 * 60
JWT_REFRESH_MARGIN_SECONDS = 2 * 60  # refresh when < 2 min of life remain (clock-skew margin)

USER_AGENT = "qbt/0.1"
REQUEST_TIMEOUT = 30.0


def finam_symbol(
    canonical: str,
    asset_class: AssetClass | None = None,
    provider_symbols: dict | None = None,
) -> str:
    """Canonical 'MOEX:SBER' -> Finam 'SBER@MISX'.

    Prefers an explicit Instrument.provider_symbols['finam'] override; otherwise appends a
    default suffix by asset class. VERIFY-ON-WINDOWS: the future-symbol suffix guess above.
    """
    if provider_symbols and "finam" in provider_symbols:
        return provider_symbols["finam"]
    secid = canonical.split(":", 1)[1] if ":" in canonical else canonical
    if asset_class == AssetClass.FUTURE:
        return f"{secid}{FINAM_FUTURE_SUFFIX}"
    return f"{secid}{FINAM_EQUITY_SUFFIX}"


class _LocalTokenBucket:
    """Minimal token-bucket rate limiter, duplicated here on purpose (NOT importing
    qbt.core.ratelimit, which is WS-A's) to avoid a cross-workstream dependency per
    architecture.md. Keep semantics in sync manually if that module changes."""

    def __init__(self, rate_per_min: int = 200):
        self.capacity = float(rate_per_min)
        self.tokens = float(rate_per_min)
        self.rate_per_sec = rate_per_min / 60.0
        self._updated = time.monotonic()
        self._lock = threading.Lock()

    def acquire(self) -> None:
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._updated
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate_per_sec)
            self._updated = now
            if self.tokens < 1.0:
                wait = (1.0 - self.tokens) / self.rate_per_sec
                time.sleep(wait)
                self.tokens = 0.0
                self._updated = time.monotonic()
            else:
                self.tokens -= 1.0


class FinamProvider:
    """MarketDataProvider over the Finam Trade API. Requires an API secret (QBT_FINAM_SECRET)."""

    name = "finam"
    capabilities = ProviderCapabilities(
        freqs=frozenset({Freq.M1, Freq.M5, Freq.H1, Freq.D1}),
        asset_classes=frozenset({AssetClass.EQUITY, AssetClass.ETF, AssetClass.FUTURE, AssetClass.BOND}),
        max_history_days=None,
        pit_universe=False,
        corporate_actions=False,
        futures_chains=False,
        needs_key=True,
        rate_limit_per_min=200,
    )

    def __init__(
        self,
        secret: str,
        base_url: str = FINAM_BASE_URL,
        session: requests.Session | None = None,
        rate_per_min: int = 200,
        timeout: float = REQUEST_TIMEOUT,
    ):
        if not secret:
            raise ProviderAuthError("FinamProvider requires a non-empty secret", provider="finam")
        self._secret = secret
        self.base_url = base_url.rstrip("/")
        self.session = session or requests.Session()
        self.session.headers.setdefault("User-Agent", USER_AGENT)
        self.timeout = timeout
        self._bucket = _LocalTokenBucket(rate_per_min)

        self._token: str | None = None
        self._token_expiry: datetime | None = None
        self._token_lock = threading.Lock()

    # -- auth / JWT lifecycle ---------------------------------------------------

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _authenticate(self) -> tuple[str, datetime]:
        url = f"{self.base_url}{FINAM_AUTH_PATH}"
        resp = self.session.post(url, json={"secret": self._secret}, timeout=self.timeout)
        if resp.status_code == 401 or resp.status_code == 403:
            raise ProviderAuthError(
                f"Finam auth rejected the secret ({resp.status_code}): {resp.text[:200]}",
                provider="finam",
            )
        if resp.status_code != 200:
            raise ProviderError(
                f"Finam auth failed: {resp.status_code} {resp.text[:200]}", provider="finam"
            )
        try:
            body = resp.json()
            token = body[FINAM_AUTH_TOKEN_FIELD]
        except (ValueError, KeyError) as exc:
            raise ProviderAuthError(
                f"Finam auth response missing '{FINAM_AUTH_TOKEN_FIELD}': {resp.text[:200]}",
                provider="finam",
            ) from exc
        expiry = self._now() + timedelta(seconds=JWT_LIFETIME_SECONDS)
        return token, expiry

    def _ensure_token(self) -> str:
        """Thread-safe: return a valid JWT, refreshing if <2min of life remain."""
        with self._token_lock:
            needs_refresh = (
                self._token is None
                or self._token_expiry is None
                or self._now() >= self._token_expiry - timedelta(seconds=JWT_REFRESH_MARGIN_SECONDS)
            )
            if needs_refresh:
                self._token, self._token_expiry = self._authenticate()
            return self._token

    # -- bars ---------------------------------------------------------------

    def fetch_bars(self, req: BarRequest) -> BarFrame:
        if req.freq not in _TIMEFRAME_BY_FREQ:
            raise ProviderError(f"finam does not support freq={req.freq!r}", provider="finam")
        timeframe = _TIMEFRAME_BY_FREQ[req.freq]
        frames: list[pd.DataFrame] = []
        for raw_symbol in req.symbols:
            symbol = finam_symbol(raw_symbol)
            df = self._fetch_bars_one(symbol, timeframe, req.start, req.end)
            if df.empty:
                continue
            df.insert(0, "symbol", raw_symbol)
            frames.append(df)
        if not frames:
            return BarFrame.empty_frame()
        return BarFrame.validate(pd.concat(frames, ignore_index=True))

    def _fetch_bars_one(self, symbol: str, timeframe: str, start: datetime, end: datetime) -> pd.DataFrame:
        token = self._ensure_token()
        self._bucket.acquire()
        url = f"{self.base_url}{FINAM_BARS_PATH_TMPL.format(symbol=symbol)}"
        params = {
            FINAM_BARS_TIMEFRAME_PARAM: timeframe,
            FINAM_BARS_START_PARAM: start.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            FINAM_BARS_END_PARAM: end.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        headers = {"Authorization": f"Bearer {token}"}
        resp = self.session.get(url, params=params, headers=headers, timeout=self.timeout)
        if resp.status_code == 429:
            raise RateLimitError("Finam rate limit exceeded", provider="finam")
        if resp.status_code in (401, 403):
            raise ProviderAuthError(
                f"Finam bars request unauthorized: {resp.status_code} {resp.text[:200]}",
                provider="finam",
            )
        if resp.status_code != 200:
            raise ProviderError(
                f"Finam bars request failed: {resp.status_code} {resp.text[:200]}", provider="finam"
            )
        body = resp.json()
        bars = body.get(FINAM_BARS_RESPONSE_KEY, [])
        if not bars:
            return pd.DataFrame()
        raw = pd.DataFrame(bars)
        return pd.DataFrame({
            "ts": pd.to_datetime(raw["timestamp"], utc=True),
            "open": pd.to_numeric(raw["open"], errors="coerce"),
            "high": pd.to_numeric(raw["high"], errors="coerce"),
            "low": pd.to_numeric(raw["low"], errors="coerce"),
            "close": pd.to_numeric(raw["close"], errors="coerce"),
            "volume": pd.to_numeric(raw["volume"], errors="coerce"),
            "value": float("nan"),
            "oi": float("nan"),
        })

    # -- unsupported for MVP scope -----------------------------------------

    def list_instruments(
        self, asof: date | None = None, asset_class: AssetClass | None = None
    ) -> list[Instrument]:
        raise ProviderError(
            "FinamProvider.list_instruments is out of MVP scope; use moex_iss for PIT universe",
            provider="finam",
        )

    def fetch_corporate_actions(self, symbol: str) -> list[CorporateAction]:
        raise ProviderError(
            "FinamProvider does not implement corporate actions; use moex_iss", provider="finam"
        )

    def fetch_futures_chain(self, asset_code: str, include_expired: bool = True) -> list[FuturesContract]:
        raise ProviderError(
            "FinamProvider does not implement futures chains; use moex_iss", provider="finam"
        )

    # -- health ---------------------------------------------------------------

    def health(self) -> ProviderHealth:
        try:
            self._ensure_token()
        except ProviderError as exc:
            return ProviderHealth(ok=False, provider=self.name, detail=str(exc))
        return ProviderHealth(ok=True, provider=self.name, detail="JWT obtained")


__all__ = [
    "FinamProvider", "finam_symbol", "FINAM_BASE_URL", "FINAM_AUTH_PATH",
    "FINAM_TIMEFRAME_M1", "FINAM_TIMEFRAME_M5", "FINAM_TIMEFRAME_H1", "FINAM_TIMEFRAME_D1",
    "JWT_LIFETIME_SECONDS", "JWT_REFRESH_MARGIN_SECONDS",
]
