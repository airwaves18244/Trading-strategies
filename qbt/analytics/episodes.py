"""Per-episode reporting for episodic strategies (doc 04-02 §7) (WS-C)."""
from __future__ import annotations

import pandas as pd


def episode_table(trades: pd.DataFrame, equity: pd.Series | None = None) -> pd.DataFrame:
    """Group the ledger by tag: per-episode pnl, duration, trade count."""
    if trades is None or not len(trades):
        return pd.DataFrame(columns=["tag", "start", "end", "n_trades", "pnl", "duration_days"])
    df = trades.copy()
    df["ts"] = pd.to_datetime(df["ts"], utc=True)
    df["tag"] = df["tag"].replace("", "untagged")
    rows = []
    for tag, g in df.groupby("tag"):
        rows.append({
            "tag": tag,
            "start": g["ts"].min(),
            "end": g["ts"].max(),
            "n_trades": int(len(g)),
            "pnl": float(g["pnl"].dropna().sum()),
            "duration_days": float((g["ts"].max() - g["ts"].min()).days),
        })
    return pd.DataFrame(rows).sort_values("start").reset_index(drop=True)
