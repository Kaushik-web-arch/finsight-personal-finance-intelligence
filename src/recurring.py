"""Recurring-expense detector.

Heuristic: same description + similar amount appearing on a roughly
constant monthly interval at least 2 times.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def detect(df: pd.DataFrame, amount_tol: float = 0.10, interval_tol_days: int = 5) -> pd.DataFrame:
    e = df[df["type"] == "Expense"].copy()
    if e.empty:
        return pd.DataFrame(columns=["description", "category", "avg_amount", "occurrences", "avg_interval_days"])

    out = []
    for desc, grp in e.groupby("description"):
        if len(grp) < 2 or not desc:
            continue
        grp = grp.sort_values("date")
        amounts = grp["amount"].to_numpy()
        # amount stability
        if amounts.mean() == 0:
            continue
        rel_std = amounts.std() / amounts.mean()
        if rel_std > amount_tol:
            continue
        # interval stability
        intervals = grp["date"].diff().dt.days.dropna().to_numpy()
        if len(intervals) == 0:
            continue
        avg_int = intervals.mean()
        if not (25 <= avg_int <= 35):  # roughly monthly
            continue
        if intervals.std() > interval_tol_days:
            continue
        out.append({
            "description": desc,
            "category": grp["category"].mode().iat[0],
            "avg_amount": float(amounts.mean()),
            "occurrences": int(len(grp)),
            "avg_interval_days": float(avg_int),
        })
    return pd.DataFrame(out).sort_values("avg_amount", ascending=False) if out else \
        pd.DataFrame(columns=["description", "category", "avg_amount", "occurrences", "avg_interval_days"])
