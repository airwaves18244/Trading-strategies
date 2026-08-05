#!/usr/bin/env python3
"""Record HTTP fixtures ("cassettes") for provider parse tests.

    python scripts/record_fixtures.py --provider moex_iss
    python scripts/record_fixtures.py --provider finam      # only if QBT_FINAM_SECRET set
    python scripts/record_fixtures.py --provider algopack   # only if QBT_ALGOPACK_TOKEN set

moex_iss fixtures are free/anonymous and recordable from anywhere with network access
(this dev container included) — that's how tests/fixtures/http/moex_iss/*.json were
produced. finam/algopack need real credentials and will only actually record on a machine
that has them (per architecture.md, that's the user's Windows box); without a key this
prints a skip message and exits 0 rather than failing the run.

Fixtures are plain JSON: {"url", "params", "status_code", "body"} where `body` is the raw
response text (so tests can do json.loads(fixture["body"]) exactly like a mocked
requests.Response.text would look).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_ROOT = REPO_ROOT / "tests" / "fixtures" / "http"

USER_AGENT = "qbt/0.1"


def _record(session: requests.Session, base_url: str, path: str, params: dict, out_path: Path,
            headers: dict | None = None) -> int:
    url = f"{base_url}{path}"
    resp = session.get(url, params=params, headers=headers, timeout=30.0)
    payload = {
        "url": resp.url,
        "path": path,
        "params": params,
        "status_code": resp.status_code,
        "body": resp.text,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    n_rows = _row_count(resp.text)
    print(f"  wrote {out_path.relative_to(REPO_ROOT)}  status={resp.status_code}  rows~={n_rows}")
    return n_rows


def _row_count(body_text: str) -> str:
    try:
        data = json.loads(body_text)
    except ValueError:
        return "n/a (non-JSON)"
    total = 0
    found_any = False
    for v in data.values():
        if isinstance(v, dict) and "data" in v and isinstance(v["data"], list):
            total += len(v["data"])
            found_any = True
    return str(total) if found_any else "0"


# --- moex_iss: free, no key needed; safe to record from any container with network access.

MOEX_ISS_BASE = "https://iss.moex.com/iss"

# name -> (path, params)
MOEX_ISS_FIXTURES: dict[str, tuple[str, dict]] = {
    "sber_daily_2023": (
        "/history/engines/stock/markets/shares/boards/TQBR/securities/SBER.json",
        {"from": "2023-01-01", "till": "2023-01-31"},
    ),
    "shares_securities_20230601": (
        "/history/engines/stock/markets/shares/boards/TQBR/securities.json",
        {"date": "2023-06-01"},
    ),
    "imoex_analytics_20230601": (
        "/statistics/engines/stock/markets/index/analytics/IMOEX.json",
        {"date": "2023-06-01", "limit": 100, "start": 0},
    ),
    "sber_dividends": (
        "/securities/SBER/dividends.json",
        {},
    ),
    "rts_series_show_expired": (
        "/statistics/engines/futures/markets/forts/series.json",
        {"asset_code": "RTS", "show_expired": 1},
    ),
    "rih5_futures_history": (
        "/history/engines/futures/markets/forts/securities/RIH5.json",
        {"from": "2025-01-10", "till": "2025-01-20"},
    ),
    "sber_candles_10m": (
        "/engines/stock/markets/shares/securities/SBER/candles.json",
        {"interval": 10, "from": "2023-06-01", "till": "2023-06-01"},
    ),
}


def record_moex_iss(out_dir: Path) -> None:
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    print(f"Recording {len(MOEX_ISS_FIXTURES)} moex_iss fixtures to {out_dir.relative_to(REPO_ROOT)}/")
    for name, (path, params) in MOEX_ISS_FIXTURES.items():
        _record(session, MOEX_ISS_BASE, path, params, out_dir / f"{name}.json")


# --- finam / algopack: need real credentials; only run for real on the user's machine.

def record_finam(out_dir: Path) -> None:
    secret = os.environ.get("QBT_FINAM_SECRET")
    if not secret:
        print("QBT_FINAM_SECRET not set — skipping finam fixture recording (expected in this "
              "sandbox; run this on the machine that holds the key).")
        return
    from qbt.data.providers.finam import FINAM_AUTH_PATH, FINAM_BARS_PATH_TMPL, FINAM_BASE_URL

    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    print(f"Recording finam fixtures to {out_dir.relative_to(REPO_ROOT)}/")
    auth_resp = session.post(f"{FINAM_BASE_URL}{FINAM_AUTH_PATH}", json={"secret": secret}, timeout=30.0)
    (out_dir / "auth.json").parent.mkdir(parents=True, exist_ok=True)
    (out_dir / "auth.json").write_text(
        json.dumps({"url": auth_resp.url, "status_code": auth_resp.status_code, "body": auth_resp.text},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"  wrote {out_dir / 'auth.json'} status={auth_resp.status_code}")
    if auth_resp.status_code != 200:
        print("  auth failed; skipping bars fixture")
        return
    token = auth_resp.json().get("token")
    bars_path = FINAM_BARS_PATH_TMPL.format(symbol="SBER@MISX")
    bars_resp = session.get(
        f"{FINAM_BASE_URL}{bars_path}",
        params={"timeframe": "TIME_FRAME_D", "interval.start_time": "2023-06-01T00:00:00Z",
                "interval.end_time": "2023-06-10T00:00:00Z"},
        headers={"Authorization": f"Bearer {token}"},
        timeout=30.0,
    )
    (out_dir / "sber_bars_d1.json").write_text(
        json.dumps({"url": bars_resp.url, "status_code": bars_resp.status_code, "body": bars_resp.text},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"  wrote {out_dir / 'sber_bars_d1.json'} status={bars_resp.status_code}")


def record_algopack(out_dir: Path) -> None:
    token = os.environ.get("QBT_ALGOPACK_TOKEN")
    if not token:
        print("QBT_ALGOPACK_TOKEN not set — skipping algopack fixture recording (expected in "
              "this sandbox; run this on the machine that holds the key).")
        return
    from qbt.data.providers.algopack import ALGOPACK_BASE

    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    print(f"Recording algopack fixtures to {out_dir.relative_to(REPO_ROOT)}/")
    for name, path in (
        ("sber_tradestats", "/eq/tradestats/SBER.json"),
        ("sber_obstats", "/eq/obstats/SBER.json"),
    ):
        resp = session.get(
            f"{ALGOPACK_BASE}{path}", params={"from": "2023-06-01", "till": "2023-06-01"},
            headers={"Authorization": f"Bearer {token}"}, timeout=30.0,
        )
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"{name}.json").write_text(
            json.dumps({"url": resp.url, "status_code": resp.status_code, "body": resp.text},
                       ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"  wrote {out_dir / f'{name}.json'} status={resp.status_code}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--provider", required=True, choices=["moex_iss", "finam", "algopack"])
    parser.add_argument("--out-dir", type=Path, default=None,
                         help="Override fixture output dir (default: tests/fixtures/http/<provider>/)")
    args = parser.parse_args(argv)

    out_dir = args.out_dir or (FIXTURES_ROOT / args.provider)
    if args.provider == "moex_iss":
        record_moex_iss(out_dir)
    elif args.provider == "finam":
        record_finam(out_dir)
    elif args.provider == "algopack":
        record_algopack(out_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
