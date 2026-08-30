"""Overspend-risk classifier.

For each historical month we label `overspent = expense > income`.
We train a LogisticRegression on a few engineered features and
predict the probability of overspending the *current* month.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import StandardScaler

from .preprocessing import monthly_income_expense


@dataclass
class OverspendResult:
    probability: float
    label: str            # "Likely to overspend" / "On track"
    accuracy: float       # train accuracy (small data)
    n_samples: int
    note: str


def predict_overspend(df: pd.DataFrame) -> OverspendResult | None:
    monthly = monthly_income_expense(df).copy()
    if len(monthly) < 4:
        return None

    monthly["overspent"] = (monthly["expense"] > monthly["income"]).astype(int)
    monthly["prev_expense"] = monthly["expense"].shift(1)
    monthly["roll3_expense"] = monthly["expense"].shift(1).rolling(3, min_periods=1).mean()
    monthly["prev_ratio"] = monthly["expense_ratio"].shift(1)
    monthly = monthly.dropna()

    if len(monthly) < 3 or monthly["overspent"].nunique() < 2:
        # not enough variation to train — fall back to a rule
        last_ratio = monthly["expense_ratio"].iloc[-1] if len(monthly) else 0
        prob = float(min(1.0, max(0.0, last_ratio)))
        return OverspendResult(
            probability=prob,
            label="Likely to overspend" if prob > 0.9 else "On track",
            accuracy=float("nan"),
            n_samples=int(len(monthly)),
            note="Not enough class variation — used fallback rule on expense ratio.",
        )

    feats = ["prev_expense", "roll3_expense", "prev_ratio"]
    X = monthly[feats].to_numpy()
    y = monthly["overspent"].to_numpy()

    scaler = StandardScaler().fit(X)
    Xs = scaler.transform(X)
    model = LogisticRegression(max_iter=1000).fit(Xs, y)
    acc = float(accuracy_score(y, model.predict(Xs)))

    # Predict for the *current* (latest) month using its own prior context
    latest = monthly.iloc[-1]
    x_next = scaler.transform([[latest["expense"], 
                                monthly["expense"].iloc[-3:].mean(),
                                latest["expense_ratio"]]])
    prob = float(model.predict_proba(x_next)[0, 1])

    return OverspendResult(
        probability=prob,
        label="Likely to overspend" if prob >= 0.5 else "On track",
        accuracy=acc,
        n_samples=int(len(monthly)),
        note=f"Logistic Regression on {len(feats)} features.",
    )
