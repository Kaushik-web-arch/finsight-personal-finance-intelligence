"""EDA aggregations consumed by the dashboard."""
from __future__ import annotations

import pandas as pd


def kpis(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"income": 0.0, "expense": 0.0, "savings": 0.0, "savings_rate": 0.0, "n_tx": 0}
    income = float(df.loc[df["type"] == "Income", "amount"].sum())
    expense = float(df.loc[df["type"] == "Expense", "amount"].sum())
    savings = income - expense
    rate = (savings / income) if income > 0 else 0.0
    return {
        "income": income, "expense": expense, "savings": savings,
        "savings_rate": rate, "n_tx": int(len(df)),
    }


def category_spend(df: pd.DataFrame) -> pd.DataFrame:
    e = df[df["type"] == "Expense"]
    if e.empty:
        return pd.DataFrame(columns=["category", "amount", "share"])
    g = e.groupby("category")["amount"].sum().reset_index()
    total = g["amount"].sum()
    g["share"] = g["amount"] / total if total > 0 else 0
    return g.sort_values("amount", ascending=False).reset_index(drop=True)


def daily_spend(df: pd.DataFrame) -> pd.DataFrame:
    e = df[df["type"] == "Expense"]
    if e.empty:
        return pd.DataFrame(columns=["date", "amount"])
    return e.groupby("date")["amount"].sum().reset_index().sort_values("date")


def weekday_pattern(df: pd.DataFrame) -> pd.DataFrame:
    e = df[df["type"] == "Expense"]
    if e.empty:
        return pd.DataFrame(columns=["day_of_week", "amount"])
    order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    g = e.groupby("day_of_week")["amount"].mean().reindex(order).reset_index()
    return g


def weekend_vs_weekday(df: pd.DataFrame) -> dict:
    e = df[df["type"] == "Expense"]
    if e.empty:
        return {"weekday_avg": 0.0, "weekend_avg": 0.0, "uplift_pct": 0.0}
    daily = e.groupby(["date", "is_weekend"])["amount"].sum().reset_index()
    wd = daily.loc[~daily["is_weekend"], "amount"].mean() if (~daily["is_weekend"]).any() else 0.0
    we = daily.loc[ daily["is_weekend"], "amount"].mean() if ( daily["is_weekend"]).any() else 0.0
    uplift = ((we - wd) / wd * 100) if wd > 0 else 0.0
    return {"weekday_avg": float(wd), "weekend_avg": float(we), "uplift_pct": float(uplift)}
