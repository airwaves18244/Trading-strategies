"""Documented CSV/parquet event schemas for data-fed strategies (Group B/C). PHASE 0 CONTRACT.

Every schema: {column -> dtype string}. dtype strings: "date", "datetime" (UTC),
"str", "float", "int". Columns suffixed "?" in REQUIRED are optional.

Strategies declare needs via Strategy.data_requirements = ("deals", ...).
Loaders must call validate_events(df, name) and raise SchemaError with a readable
message listing missing/badly-typed columns.
"""
from __future__ import annotations

import pandas as pd

from qbt.core.errors import SchemaError

#: schema name -> ordered {column: dtype}; optional columns end with "?"
EVENT_SCHEMAS: dict[str, dict[str, str]] = {
    # merger arbitrage (01-05)
    "deals": {
        "target_symbol": "str", "announce_date": "date", "offer_price": "float",
        "consideration": "str",            # cash|stock|mixed
        "acquirer_symbol?": "str", "exchange_ratio?": "float",
        "close_date?": "date", "outcome?": "str",   # completed|terminated|pending
        "terminate_date?": "date",
    },
    # VIX-style vol futures curve (05-04, 06-02)
    "vol_futures_curve": {
        "date": "date", "expiry": "date", "settle": "float", "symbol?": "str",
        "spot_index?": "float",
    },
    # options surface for VRP/dispersion (06-01, 06-03)
    "options_surface": {
        "date": "date", "expiry": "date", "strike": "float", "cp": "str",
        "iv": "float", "bid?": "float", "ask?": "float", "delta?": "float",
        "underlying_symbol?": "str", "underlying_price?": "float",
    },
    # PEAD (07-01)
    "earnings_events": {
        "symbol": "str", "report_ts": "datetime", "eps_actual": "float",
        "eps_consensus?": "float", "eps_yoy_prior?": "float",
    },
    # index add/delete (07-02); partially auto-derivable from ISS PIT constituents
    "index_events": {
        "symbol": "str", "index_name": "str", "action": "str",   # add|delete
        "announce_date": "date", "effective_date": "date",
    },
    # buybacks & insider buying (07-03)
    "insider_buyback_events": {
        "symbol": "str", "event_date": "date", "kind": "str",    # buyback|insider_buy
        "pct_of_shares?": "float", "value_rub?": "float", "n_insiders?": "int",
    },
    # IPO lockups (07-04)
    "ipo_lockups": {
        "symbol": "str", "ipo_date": "date", "lockup_expiry": "date",
        "locked_to_float?": "float", "vc_backed?": "int",
    },
    # macro calendar (07-05)
    "macro_calendar": {
        "release_ts": "datetime", "kind": "str",  # cbr_rate|cpi|fomc|nfp|...
        "actual?": "float", "consensus?": "float", "surprise_std?": "float",
    },
    # point-in-time fundamentals for value/quality/seasonality (08-01, 09-03)
    "fundamentals_pit": {
        "symbol": "str", "asof_date": "date",     # when the data became public
        "period_end": "date", "metric": "str",    # eps|book|ebitda|fcf|sales|...
        "value": "float",
    },
    # commodity index roll calendar (09-02)
    "roll_calendar": {
        "index_name": "str", "roll_start": "date", "roll_end": "date",
        "asset_code": "str",
    },
    # crypto funding (10-01); bars for perp/spot go through the normal FileProvider
    "funding_rates": {
        "ts": "datetime", "symbol": "str", "venue": "str", "funding_rate": "float",
        "interval_hours?": "float",
    },
    # convertibles terms (01-07, Group C)
    "convert_terms": {
        "bond_symbol": "str", "equity_symbol": "str", "issue_date": "date",
        "maturity": "date", "conversion_ratio": "float", "coupon": "float",
        "call_price?": "float",
    },
    # ETF iNAV / NAV (01-04, Group C live variant)
    "nav_series": {
        "date": "date", "symbol": "str", "nav": "float", "price?": "float",
    },
    # multi-venue quotes (10-02, Group C)
    "multi_venue_quotes": {
        "ts": "datetime", "symbol": "str", "venue": "str",
        "bid": "float", "ask": "float", "bid_size?": "float", "ask_size?": "float",
    },
}

_DTYPE_CHECKS = {
    "date": lambda s: pd.to_datetime(s, errors="raise"),
    "datetime": lambda s: pd.to_datetime(s, utc=True, errors="raise"),
    "str": lambda s: s.astype(str),
    "float": lambda s: pd.to_numeric(s, errors="raise"),
    "int": lambda s: pd.to_numeric(s, errors="raise").astype("Int64"),
}


def validate_events(df: pd.DataFrame, schema_name: str) -> pd.DataFrame:
    """Validate & coerce an event dataframe against a named schema.

    Returns a coerced copy (dates -> datetime64, datetimes -> UTC).
    Raises SchemaError with a readable message on any problem.
    """
    if schema_name not in EVENT_SCHEMAS:
        raise SchemaError(f"Unknown event schema '{schema_name}'. Known: {sorted(EVENT_SCHEMAS)}")
    spec = EVENT_SCHEMAS[schema_name]
    out = pd.DataFrame(index=df.index)
    problems: list[str] = []
    for col, dtype in spec.items():
        optional = col.endswith("?")
        name = col.rstrip("?")
        if name not in df.columns:
            if not optional:
                problems.append(f"missing required column '{name}' ({dtype})")
            continue
        try:
            out[name] = _DTYPE_CHECKS[dtype](df[name])
        except Exception as e:  # noqa: BLE001 - surface as schema problem
            problems.append(f"column '{name}' not coercible to {dtype}: {e}")
    if problems:
        raise SchemaError(
            f"Event data does not match schema '{schema_name}':\n  - " + "\n  - ".join(problems)
        )
    return out


__all__ = ["EVENT_SCHEMAS", "validate_events"]
