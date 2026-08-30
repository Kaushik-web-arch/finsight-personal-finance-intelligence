"""Anomaly detection — Z-score (global) + IQR (per category)."""
from __future__ import annotations

import numpy as np
import pandas as pd


def zscore_anomalies(df: pd.DataFrame, threshold: float = 2.5) -> pd.DataFrame:
    e = df[df["type"] == "Expense"].copy()
    if e.empty:
        return e.assign(zscore=[], reason=[])
    mu, sd = e["amount"].mean(), e["amount"].std(ddof=0)
    if sd == 0 or np.isnan(sd):
        return e.iloc[0:0].assign(zscore=[], reason=[])
    e["zscore"] = (e["amount"] - mu) / sd
    flagged = e[e["zscore"].abs() >= threshold].copy()
    flagged["reason"] = flagged["zscore"].apply(
        lambda z: f"Z-score {z:+.2f} (>|{threshold}|)"
    )
    return flagged.sort_values("amount", ascending=False)


def iqr_anomalies_per_category(df: pd.DataFrame, k: float = 1.5) -> pd.DataFrame:
    e = df[df["type"] == "Expense"].copy()
    if e.empty:
        return e.assign(reason=[])
    rows = []
    for cat, grp in e.groupby("category"):
        if len(grp) < 4:
            continue
        q1, q3 = grp["amount"].quantile([0.25, 0.75])
        iqr = q3 - q1
        upper = q3 + k * iqr
        cat_mean = grp["amount"].mean()
        for _, r in grp[grp["amount"] > upper].iterrows():
            rows.append({
                **r.to_dict(),
                "reason": (
                    f"₹{r['amount']:,.0f} on {cat} is unusually high "
                    f"vs typical ₹{cat_mean:,.0f}"
                ),
            })
    return pd.DataFrame(rows).sort_values("amount", ascending=False) if rows else \
        pd.DataFrame(columns=list(e.columns) + ["reason"])
