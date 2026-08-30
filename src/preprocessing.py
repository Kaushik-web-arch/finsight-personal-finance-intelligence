"""Cleaning + feature engineering."""
from __future__ import annotations

import numpy as np
import pandas as pd


def clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if df.empty:
        return df

    # dtypes
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")

    # missing values
    df = df.dropna(subset=["date", "amount"])
    df["category"] = df["category"].fillna("Other").astype(str).str.strip().str.title()
    df["description"] = df["description"].fillna("").astype(str).str.strip()
    df["type"] = df["type"].fillna("Expense").astype(str).str.strip().str.title()

    # dedup
    df = df.drop_duplicates(subset=["date", "amount", "category", "description", "type"])

    # negative amounts → absolute
    df["amount"] = df["amount"].abs()
    return df.reset_index(drop=True)


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Engineer time + behavioral features."""
    df = clean(df)
    if df.empty:
        return df

    # Make feature engineering safe to run more than once on the same frame.
    df = df.drop(columns=["rolling_7d_expense"], errors="ignore")

    df["year"]        = df["date"].dt.year
    df["month"]       = df["date"].dt.month
    df["month_str"]   = df["date"].dt.strftime("%Y-%m")
    df["day"]         = df["date"].dt.day
    df["day_of_week"] = df["date"].dt.day_name()
    df["dow_num"]     = df["date"].dt.dayofweek
    df["is_weekend"]  = df["dow_num"] >= 5

    # rolling 7-day expense (per row)
    expense_only = df[df["type"] == "Expense"].copy()
    daily = expense_only.groupby("date")["amount"].sum().sort_index()
    rolling7 = daily.rolling(7, min_periods=1).mean()
    df = df.merge(
        rolling7.rename("rolling_7d_expense"),
        left_on="date", right_index=True, how="left",
    )
    df["rolling_7d_expense"] = df["rolling_7d_expense"].fillna(0)

    return df


def monthly_income_expense(df: pd.DataFrame) -> pd.DataFrame:
    """Return per-month income, expense, savings, expense_ratio."""
    if df.empty:
        return pd.DataFrame(columns=["month_str", "income", "expense", "savings", "expense_ratio"])

    g = (
        df.groupby(["month_str", "type"])["amount"].sum().unstack(fill_value=0).reset_index()
    )
    for col in ("Income", "Expense"):
        if col not in g.columns:
            g[col] = 0.0
    g = g.rename(columns={"Income": "income", "Expense": "expense"})
    g["savings"] = g["income"] - g["expense"]
    g["expense_ratio"] = np.where(g["income"] > 0, g["expense"] / g["income"], np.nan)
    return g.sort_values("month_str").reset_index(drop=True)
