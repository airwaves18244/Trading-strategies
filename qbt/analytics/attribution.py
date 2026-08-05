"""Cost & instrument attribution (WS-C)."""
from __future__ import annotations

import pandas as pd


def cost_attribution(costs: pd.DataFrame) -> pd.DataFrame:
    """Total and annualized drag per component (fractions of NAV)."""
    total = costs.sum()
    ppy = 252.0
    ann = costs.mean() * ppy
    return pd.DataFrame({"total": total, "ann_drag": ann})


def instrument_contribution(weights: pd.DataFrame, returns: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    """Cumulative gross PnL contribution per instrument."""
    contrib = (weights.fillna(0.0) * returns.reindex_like(weights).fillna(0.0)).sum()
    out = contrib.sort_values(ascending=False).to_frame("contribution")
    return pd.concat([out.head(top_n), out.tail(min(top_n, max(0, len(out) - top_n)))])
