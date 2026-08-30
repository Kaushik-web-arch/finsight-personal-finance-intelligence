"""Next-month expense forecasting.

Two models, both trained on monthly aggregates:
  - Moving Average (3-month)
  - Linear Regression on [month_index, prev_month_expense, rolling_3m_mean]
The better of the two (lower MAE on a held-out tail) is returned.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score

from .preprocessing import monthly_income_expense


@dataclass
class Forecast:
    next_month: str
    predicted_expense: float
    model_used: str
    mae: float
    r2: float
    history: pd.DataFrame  # month_str, expense, predicted (for chart)


def _next_month_str(last: str) -> str:
    ts = pd.Period(last, freq="M") + 1
    return str(ts)


def forecast(df: pd.DataFrame) -> Forecast | None:
    monthly = monthly_income_expense(df)
    if len(monthly) < 4:
        return None

    monthly = monthly.copy()
    monthly["t"] = np.arange(len(monthly))
    monthly["prev"] = monthly["expense"].shift(1)
    monthly["roll3"] = monthly["expense"].shift(1).rolling(3, min_periods=1).mean()
    train = monthly.dropna()

    if len(train) < 3:
        return None

    X = train[["t", "prev", "roll3"]].to_numpy()
    y = train["expense"].to_numpy()

    # walk-forward eval on the last point
    split = max(1, len(train) - 1)
    Xtr, Xte = X[:split], X[split:]
    ytr, yte = y[:split], y[split:]

    lr = LinearRegression().fit(Xtr, ytr)
    lr_pred_te = lr.predict(Xte)
    lr_mae = mean_absolute_error(yte, lr_pred_te)

    ma_pred_te = np.array([train["roll3"].iloc[split:].mean()])
    ma_mae = mean_absolute_error(yte, ma_pred_te)

    # Forecast the next month
    last_row = monthly.iloc[-1]
    next_t = last_row["t"] + 1
    next_prev = last_row["expense"]
    next_roll3 = monthly["expense"].iloc[-3:].mean()
    x_next = np.array([[next_t, next_prev, next_roll3]])

    if lr_mae <= ma_mae:
        model_used = "Linear Regression"
        pred = float(lr.predict(x_next)[0])
        mae = float(lr_mae)
        # in-sample fit for chart
        in_pred = lr.predict(X)
        r2 = float(r2_score(y, in_pred))
        history = train[["month_str", "expense"]].assign(predicted=in_pred)
    else:
        model_used = "3-month Moving Average"
        pred = float(next_roll3)
        mae = float(ma_mae)
        r2 = float("nan")
        history = train[["month_str", "expense"]].assign(predicted=train["roll3"].values)

    return Forecast(
        next_month=_next_month_str(monthly["month_str"].iloc[-1]),
        predicted_expense=max(0.0, pred),
        model_used=model_used,
        mae=mae,
        r2=r2,
        history=history.reset_index(drop=True),
    )
