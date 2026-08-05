"""Synthetic data generators with analytic answers. PHASE 0 signatures; bodies = WS-C (engine).

Shared by every workstream's tests. make_context() is the standard way to get a
DataContext without any network/provider.
"""
from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from qbt.core.errors import SchemaError
from qbt.core.types import AssetClass, Freq, Instrument
from qbt.data.schemas import EVENT_SCHEMAS, validate_events
from qbt.engine.context import DataContext

#: Realistic MOEX-flavoured names so synthetic tests read naturally.
_TICKERS = (
    "SBER", "GAZP", "LKOH", "GMKN", "ROSN",
    "NVTK", "YDEX", "MGNT", "MTSS", "TATN",
)


def business_calendar(start: str, end: str) -> pd.DatetimeIndex:
    """UTC business-day calendar (no MOEX holidays — synthetic)."""
    return pd.bdate_range(start, end, tz="UTC")


# --------------------------------------------------------------------------- #
# helpers                                                                      #
# --------------------------------------------------------------------------- #

def _symbols(n: int) -> list[str]:
    out = []
    for i in range(n):
        out.append(f"MOEX:{_TICKERS[i]}" if i < len(_TICKERS) else f"MOEX:SYN{i}")
    return out


def _instruments(symbols: list[str], asset_class: AssetClass = AssetClass.EQUITY
                 ) -> dict[str, Instrument]:
    return {
        s: Instrument(
            symbol=s,
            exchange="MOEX",
            asset_class=asset_class,
            currency="RUB",
            board="TQBR" if asset_class == AssetClass.EQUITY else None,
            sector=f"SEC{i % 3}",
            provider_symbols={"moex_iss": s.split(":")[-1]},
        )
        for i, s in enumerate(symbols)
    }


def _ohlc_from_close(close: pd.DataFrame, wiggle: float = 0.003
                     ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Deterministic OHLC envelope around a close path (open = previous close)."""
    open_ = close.shift(1)
    open_.iloc[0] = close.iloc[0]
    hi = np.maximum(open_.to_numpy(), close.to_numpy()) * (1.0 + wiggle)
    lo = np.minimum(open_.to_numpy(), close.to_numpy()) * (1.0 - wiggle)
    high = pd.DataFrame(hi, index=close.index, columns=close.columns)
    low = pd.DataFrame(lo, index=close.index, columns=close.columns)
    return open_, high, low


def _assemble(
    close: pd.DataFrame,
    *,
    open_: pd.DataFrame | None = None,
    high: pd.DataFrame | None = None,
    low: pd.DataFrame | None = None,
    volume: pd.DataFrame | None = None,
    total_return: pd.DataFrame | None = None,
    asset_class: AssetClass = AssetClass.EQUITY,
    freq: Freq = Freq.D1,
    delisting_return: pd.DataFrame | None = None,
    universe_mask: pd.DataFrame | None = None,
) -> DataContext:
    """Build a fully-populated DataContext from a close frame."""
    cal = pd.DatetimeIndex(close.index)
    syms = list(close.columns)
    if open_ is None or high is None or low is None:
        o, h, lo = _ohlc_from_close(close)
        open_ = open_ if open_ is not None else o
        high = high if high is not None else h
        low = low if low is not None else lo
    if volume is None:
        volume = pd.DataFrame(1_000_000.0, index=cal, columns=syms)
    if total_return is None:
        total_return = close.copy()
    if universe_mask is None:
        universe_mask = pd.DataFrame(True, index=cal, columns=syms)
    value = volume * close
    return DataContext(
        calendar=cal,
        instruments=_instruments(syms, asset_class),
        open=open_, high=high, low=low, close=close,
        total_return=total_return, volume=volume, value=value,
        universe_mask=universe_mask,
        delisting_return=delisting_return,
        freq=freq,
        benchmark=close.iloc[:, 0].copy(),
    )


# --------------------------------------------------------------------------- #
# contexts                                                                     #
# --------------------------------------------------------------------------- #

def make_context(
    n_symbols: int = 5,
    start: str = "2015-01-05",
    end: str = "2023-12-29",
    drift: float | list[float] = 0.0002,
    vol: float | list[float] = 0.01,
    seed: int = 7,
    freq: Freq = Freq.D1,
) -> DataContext:
    """GBM-ish random universe, full universe_mask, volume/value filled,
    total_return == close (no dividends). Deterministic under seed."""
    cal = business_calendar(start, end)
    n = len(cal)
    if n == 0:
        raise ValueError("empty calendar")
    syms = _symbols(n_symbols)
    mu = np.asarray(np.broadcast_to(np.asarray(drift, dtype=float), (n_symbols,)), dtype=float)
    sg = np.asarray(np.broadcast_to(np.asarray(vol, dtype=float), (n_symbols,)), dtype=float)

    rng = np.random.default_rng(seed)
    shocks = rng.standard_normal((n, n_symbols))
    rets = mu[None, :] + sg[None, :] * shocks
    rets[0, :] = 0.0
    px = 100.0 * np.cumprod(1.0 + rets, axis=0)
    close = pd.DataFrame(px, index=cal, columns=syms)

    open_, high, low = _ohlc_from_close(close, wiggle=0.004)
    vol_shocks = rng.lognormal(mean=0.0, sigma=0.3, size=(n, n_symbols))
    volume = pd.DataFrame(1_000_000.0 * vol_shocks, index=cal, columns=syms)
    return _assemble(close, open_=open_, high=high, low=low, volume=volume, freq=freq)


def constant_drift_context(mu_daily: float = 0.001, n_days: int = 500) -> DataContext:
    """Single symbol, exact constant simple return each bar: closed-form equity
    (1+mu)^t for buy-and-hold — the analytic anchor for engine tests."""
    cal = pd.bdate_range("2015-01-05", periods=int(n_days), tz="UTC")
    px = 100.0 * np.power(1.0 + mu_daily, np.arange(len(cal), dtype=float))
    close = pd.DataFrame({"MOEX:SBER": px}, index=cal)
    return _assemble(close)


def piecewise_vol_context(vols: tuple[float, ...] = (0.005, 0.02), block: int = 120) -> DataContext:
    """Vol regime blocks — vol-target exposure must equal target/realized at
    known dates (up to estimator lag)."""
    if not vols:
        raise ValueError("vols must be non-empty")
    seq: list[float] = []
    for v in vols:
        # deterministic +v, -v, +v, ... => EWMA(r^2) == v^2 exactly inside a block
        for i in range(int(block)):
            seq.append(float(v) if i % 2 == 0 else -float(v))
    rets = np.asarray(seq, dtype=float)
    rets[0] = 0.0
    cal = pd.bdate_range("2015-01-05", periods=len(rets), tz="UTC")
    px = 100.0 * np.cumprod(1.0 + rets)
    close = pd.DataFrame({"MOEX:SBER": px}, index=cal)
    return _assemble(close)


def sawtooth_pair_context(period: int = 20, amp: float = 0.05) -> DataContext:
    """Two cointegrated series with deterministic sawtooth spread — pairs
    strategy must enter/exit on enumerable dates; PnL hand-computable."""
    n_periods = 10
    n = int(period) * n_periods
    cal = pd.bdate_range("2015-01-05", periods=n, tz="UTC")
    t = np.arange(n)
    # sawtooth in [-1, 1): ramps up over `period` bars then resets
    saw = 2.0 * ((t % int(period)) / float(period)) - 1.0
    a = np.full(n, 100.0)
    b = 100.0 * (1.0 + float(amp) * saw)
    close = pd.DataFrame({"MOEX:SBER": a, "MOEX:GAZP": b}, index=cal)
    return _assemble(close)


def bid_ask_bounce_context(half_spread: float = 0.005, n_days: int = 750) -> DataContext:
    """Flat mid with alternating trade prints at bid/ask: reversal signals on
    trade prices show fake alpha that MUST die under one-day-wait execution —
    the deterministic ground for the lag canary."""
    n = int(n_days)
    cal = pd.bdate_range("2015-01-05", periods=n, tz="UTC")
    mid = 100.0
    sign = np.where(np.arange(n) % 2 == 0, 1.0, -1.0)
    px = mid * (1.0 + float(half_spread) * sign)
    close = pd.DataFrame({"MOEX:SBER": px}, index=cal)
    open_ = pd.DataFrame({"MOEX:SBER": np.full(n, mid)}, index=cal)
    high = pd.DataFrame({"MOEX:SBER": np.full(n, mid * (1.0 + float(half_spread)))}, index=cal)
    low = pd.DataFrame({"MOEX:SBER": np.full(n, mid * (1.0 - float(half_spread)))}, index=cal)
    return _assemble(close, open_=open_, high=high, low=low)


def known_drawdown_context() -> tuple[DataContext, dict[str, float]]:
    """Hand-built path with known max_dd, dd duration and per-year numbers;
    returns (ctx, expected_metrics)."""
    up1, dn, up2 = 100, 50, 400
    r_up1, r_dn, r_up2 = 0.001, -0.004, 0.002
    rets = np.concatenate([
        np.full(up1, r_up1),
        np.full(dn, r_dn),
        np.full(up2, r_up2),
    ])
    rets = np.concatenate([[0.0], rets])          # first bar has no return
    n = len(rets)
    cal = pd.bdate_range("2015-01-05", periods=n, tz="UTC")
    px = 100.0 * np.cumprod(1.0 + rets)
    close = pd.DataFrame({"MOEX:SBER": px}, index=cal)
    ctx = _assemble(close)

    # ---- expected metrics, computed independently of qbt.analytics ----------
    r = rets[1:]                                   # the realised return stream
    eq = np.cumprod(1.0 + r)
    peak = np.maximum.accumulate(eq)
    dd = eq / peak - 1.0
    max_dd = float(dd.min())
    trough_i = int(np.argmin(dd))
    peak_i = int(np.argmax(eq[: trough_i + 1]))
    rec = np.where(eq[trough_i:] >= peak[trough_i])[0]
    end_i = int(trough_i + rec[0]) if len(rec) else int(len(eq) - 1)
    ppy = 252.0
    mean, sd = float(r.mean()), float(r.std(ddof=1))
    years = len(r) / ppy
    expected = {
        "max_dd": max_dd,
        "dd_peak_idx": float(peak_i),
        "dd_trough_idx": float(trough_i),
        "dd_end_idx": float(end_i),
        "dd_duration_days": float(end_i - peak_i),
        "ann_vol": sd * np.sqrt(ppy),
        "sharpe": mean / sd * np.sqrt(ppy),
        "cagr": float(eq[-1] ** (1.0 / years) - 1.0),
        "total_return": float(eq[-1] - 1.0),
        "n_obs": float(len(r)),
        "hit_rate": float((r > 0).sum() / (r != 0).sum()),
    }
    expected["calmar"] = expected["cagr"] / abs(max_dd)
    return ctx, expected


# --------------------------------------------------------------------------- #
# event fixtures                                                               #
# --------------------------------------------------------------------------- #

def _event_dates(calendar: pd.DatetimeIndex, n: int) -> pd.DatetimeIndex:
    cal = pd.DatetimeIndex(calendar)
    if len(cal) == 0:
        raise ValueError("event_fixture needs a non-empty calendar")
    lo, hi = int(0.05 * (len(cal) - 1)), int(0.85 * (len(cal) - 1))
    if hi <= lo:
        lo, hi = 0, len(cal) - 1
    idx = np.linspace(lo, hi, max(int(n), 1)).astype(int)
    return cal[idx]


def event_fixture(schema_name: str, symbols: list[str], calendar: pd.DatetimeIndex,
                  n_events: int = 12, seed: int = 7) -> pd.DataFrame:
    """Generate a valid synthetic event table for any EVENT_SCHEMAS entry, so
    Group B/C strategies run green with zero user data."""
    if schema_name not in EVENT_SCHEMAS:
        raise SchemaError(f"Unknown event schema '{schema_name}'. Known: {sorted(EVENT_SCHEMAS)}")
    if not symbols:
        raise ValueError("event_fixture needs at least one symbol")
    rng = np.random.default_rng(seed)
    n = max(int(n_events), 1)
    dates = _event_dates(calendar, n)
    naive = pd.DatetimeIndex(dates).tz_convert("UTC").tz_localize(None).normalize()
    syms = [symbols[i % len(symbols)] for i in range(n)]
    cal = pd.DatetimeIndex(calendar)
    last = cal[-1].tz_convert("UTC").tz_localize(None).normalize()

    def fwd(days: int) -> pd.DatetimeIndex:
        return pd.DatetimeIndex(np.minimum((naive + pd.Timedelta(days=days)).to_numpy(),
                                           last.to_numpy()))

    if schema_name == "deals":
        df = pd.DataFrame({
            "target_symbol": syms,
            "announce_date": naive,
            "offer_price": np.round(100.0 + rng.uniform(0, 50, n), 2),
            "consideration": ["cash" if i % 3 else "stock" for i in range(n)],
            "acquirer_symbol": [symbols[(i + 1) % len(symbols)] for i in range(n)],
            "exchange_ratio": np.round(rng.uniform(0.5, 2.0, n), 4),
            "close_date": fwd(90),
            "outcome": ["completed" if i % 4 else "terminated" for i in range(n)],
            "terminate_date": pd.NaT,
        })
    elif schema_name == "vol_futures_curve":
        rows = []
        for d, nd in zip(dates, naive, strict=True):
            spot = 20.0 + 5.0 * rng.random()
            for k in range(1, 4):
                rows.append({
                    "date": nd, "expiry": nd + pd.Timedelta(days=30 * k),
                    "settle": round(spot * (1.0 + 0.02 * k), 4),
                    "symbol": f"VX{k}", "spot_index": round(spot, 4),
                })
        df = pd.DataFrame(rows)
    elif schema_name == "options_surface":
        rows = []
        for nd, s in zip(naive, syms, strict=True):
            under = 100.0 + 10.0 * rng.random()
            for k in (1, 2):
                for strike in (0.9, 1.0, 1.1):
                    for cp in ("c", "p"):
                        rows.append({
                            "date": nd, "expiry": nd + pd.Timedelta(days=30 * k),
                            "strike": round(under * strike, 2), "cp": cp,
                            "iv": round(0.25 + 0.05 * abs(strike - 1.0) * 10, 4),
                            "bid": 1.0, "ask": 1.2, "delta": round(0.5 * strike, 4),
                            "underlying_symbol": s, "underlying_price": round(under, 4),
                        })
        df = pd.DataFrame(rows)
    elif schema_name == "earnings_events":
        df = pd.DataFrame({
            "symbol": syms,
            "report_ts": pd.DatetimeIndex(dates),
            "eps_actual": np.round(rng.normal(10.0, 2.0, n), 4),
            "eps_consensus": np.round(rng.normal(10.0, 1.0, n), 4),
            "eps_yoy_prior": np.round(rng.normal(9.0, 1.0, n), 4),
        })
    elif schema_name == "index_events":
        df = pd.DataFrame({
            "symbol": syms,
            "index_name": ["IMOEX"] * n,
            "action": ["add" if i % 2 == 0 else "delete" for i in range(n)],
            "announce_date": naive,
            "effective_date": fwd(14),
        })
    elif schema_name == "insider_buyback_events":
        df = pd.DataFrame({
            "symbol": syms,
            "event_date": naive,
            "kind": ["buyback" if i % 2 == 0 else "insider_buy" for i in range(n)],
            "pct_of_shares": np.round(rng.uniform(0.1, 3.0, n), 4),
            "value_rub": np.round(rng.uniform(1e7, 1e9, n), 2),
            "n_insiders": rng.integers(1, 5, n),
        })
    elif schema_name == "ipo_lockups":
        df = pd.DataFrame({
            "symbol": syms,
            "ipo_date": naive,
            "lockup_expiry": fwd(180),
            "locked_to_float": np.round(rng.uniform(0.5, 3.0, n), 4),
            "vc_backed": (np.arange(n) % 2).astype(int),
        })
    elif schema_name == "macro_calendar":
        kinds = ["cbr_rate", "cpi", "fomc", "nfp"]
        df = pd.DataFrame({
            "release_ts": pd.DatetimeIndex(dates),
            "kind": [kinds[i % len(kinds)] for i in range(n)],
            "actual": np.round(rng.normal(0.0, 1.0, n), 4),
            "consensus": np.round(rng.normal(0.0, 1.0, n), 4),
            "surprise_std": np.round(rng.normal(0.0, 1.0, n), 4),
        })
    elif schema_name == "fundamentals_pit":
        metrics = ["eps", "book", "ebitda", "fcf", "sales"]
        rows = []
        for nd, s in zip(naive, syms, strict=True):
            for m in metrics:
                rows.append({
                    "symbol": s, "asof_date": nd,
                    "period_end": nd - pd.Timedelta(days=45),
                    "metric": m, "value": round(float(rng.uniform(1.0, 100.0)), 4),
                })
        df = pd.DataFrame(rows)
    elif schema_name == "roll_calendar":
        df = pd.DataFrame({
            "index_name": ["GSCI"] * n,
            "roll_start": naive,
            "roll_end": fwd(5),
            "asset_code": [s.split(":")[-1] for s in syms],
        })
    elif schema_name == "funding_rates":
        df = pd.DataFrame({
            "ts": pd.DatetimeIndex(dates),
            "symbol": syms,
            "venue": ["binance" if i % 2 == 0 else "bybit" for i in range(n)],
            "funding_rate": np.round(rng.normal(0.0001, 0.0002, n), 8),
            "interval_hours": np.full(n, 8.0),
        })
    elif schema_name == "convert_terms":
        df = pd.DataFrame({
            "bond_symbol": [f"{s}-CB" for s in syms],
            "equity_symbol": syms,
            "issue_date": naive,
            "maturity": fwd(1000),
            "conversion_ratio": np.round(rng.uniform(5.0, 20.0, n), 4),
            "coupon": np.round(rng.uniform(0.0, 0.08, n), 4),
            "call_price": np.round(rng.uniform(100.0, 120.0, n), 2),
        })
    elif schema_name == "nav_series":
        rows = []
        for nd, s in zip(naive, syms, strict=True):
            nav = 100.0 + 10.0 * rng.random()
            rows.append({"date": nd, "symbol": s, "nav": round(nav, 4),
                         "price": round(nav * (1 + rng.normal(0, 0.002)), 4)})
        df = pd.DataFrame(rows)
    elif schema_name == "multi_venue_quotes":
        rows = []
        for d, s in zip(dates, syms, strict=True):
            mid = 100.0 + 10.0 * rng.random()
            for venue in ("binance", "kraken"):
                rows.append({"ts": d, "symbol": s, "venue": venue,
                             "bid": round(mid * 0.999, 4), "ask": round(mid * 1.001, 4),
                             "bid_size": 10.0, "ask_size": 12.0})
        df = pd.DataFrame(rows)
    else:  # pragma: no cover - EVENT_SCHEMAS fully covered above
        raise SchemaError(f"event_fixture has no generator for '{schema_name}'")

    return validate_events(df, schema_name)


__all__ = [
    "business_calendar", "make_context", "constant_drift_context",
    "piecewise_vol_context", "sawtooth_pair_context", "bid_ask_bounce_context",
    "known_drawdown_context", "event_fixture",
]
