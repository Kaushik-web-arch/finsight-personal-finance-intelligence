"""Goal-based monthly spending planner.

The planner turns transaction history into an actionable answer to a common
question: "How much can I safely spend for the rest of this month?"
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd

from .preprocessing import add_features
from .recurring import detect as detect_recurring


@dataclass
class MonthlyPlan:
    month: str
    income: float
    spent: float
    savings_goal: float
    saved_so_far: float
    committed_remaining: float
    safe_to_spend: float
    shortfall: float
    days_remaining: int
    daily_allowance: float
    projected_expense: float
    projected_savings: float
    status: str
    message: str
    pending_recurring: pd.DataFrame


def _as_timestamp(value: date | pd.Timestamp | None) -> pd.Timestamp:
    return pd.Timestamp(value or date.today()).normalize()


def _current_rows(df: pd.DataFrame, as_of: pd.Timestamp) -> tuple[pd.DataFrame, pd.DataFrame]:
    required = {"date", "amount", "type", "description", "month_str", "day"}
    featured = df.copy() if required.issubset(df.columns) else add_features(df)
    if featured.empty:
        return featured, featured
    featured["date"] = pd.to_datetime(featured["date"], errors="coerce")
    month = as_of.strftime("%Y-%m")
    current = featured[
        (featured["month_str"] == month) & (featured["date"] <= as_of)
    ].copy()
    return featured, current


def _pending_recurring(featured: pd.DataFrame, current: pd.DataFrame,
                       as_of: pd.Timestamp) -> pd.DataFrame:
    columns = ["description", "category", "expected_amount", "due_day", "due_status"]
    detected = detect_recurring(featured)
    if detected.empty:
        return pd.DataFrame(columns=columns)

    paid_descriptions = set(
        current.loc[current["type"] == "Expense", "description"].astype(str)
    )
    rows = []
    days_in_month = int(as_of.days_in_month)
    for item in detected.itertuples(index=False):
        if item.description in paid_descriptions:
            continue
        history = featured[
            (featured["type"] == "Expense")
            & (featured["description"] == item.description)
        ]
        due_day = int(round(history["day"].median())) if not history.empty else 1
        due_day = max(1, min(due_day, days_in_month))
        delta = due_day - as_of.day
        if delta > 0:
            due_status = f"Due in {delta} day{'s' if delta != 1 else ''}"
        elif delta == 0:
            due_status = "Due today"
        else:
            due_status = f"Overdue by {abs(delta)} day{'s' if delta != -1 else ''}"
        rows.append({
            "description": item.description,
            "category": item.category,
            "expected_amount": float(item.avg_amount),
            "due_day": due_day,
            "due_status": due_status,
        })
    return pd.DataFrame(rows, columns=columns).sort_values("due_day").reset_index(drop=True)


def build_monthly_plan(df: pd.DataFrame, savings_goal: float = 0.0,
                       as_of: date | pd.Timestamp | None = None) -> MonthlyPlan:
    """Build a conservative safe-to-spend plan for the month containing ``as_of``."""
    as_of_ts = _as_timestamp(as_of)
    featured, current = _current_rows(df, as_of_ts)
    goal = max(0.0, float(savings_goal))

    income = float(current.loc[current["type"] == "Income", "amount"].sum())
    spent = float(current.loc[current["type"] == "Expense", "amount"].sum())
    pending = _pending_recurring(featured, current, as_of_ts)
    committed = float(pending["expected_amount"].sum()) if not pending.empty else 0.0

    available = income - spent - goal - committed
    safe_to_spend = max(0.0, available)
    shortfall = max(0.0, -available)
    days_remaining = max(1, int(as_of_ts.days_in_month - as_of_ts.day + 1))
    daily_allowance = safe_to_spend / days_remaining

    elapsed_days = max(1, int(as_of_ts.day))
    pace_projection = spent / elapsed_days * int(as_of_ts.days_in_month)
    projected_expense = max(spent + committed, pace_projection)
    projected_savings = income - projected_expense

    if income <= 0:
        status = "Add income"
        message = "Add this month's income to calculate a reliable spending allowance."
    elif goal > income:
        status = "Goal too high"
        message = "The savings goal is higher than this month's recorded income."
    elif available < 0:
        status = "Over plan"
        message = f"Your plan is short by ₹{shortfall:,.0f}. Reduce spending or adjust the goal."
    elif projected_savings < goal:
        status = "At risk"
        message = "Your current spending pace may miss the savings goal."
    else:
        status = "On track"
        message = "Your spending pace supports the savings goal."

    return MonthlyPlan(
        month=as_of_ts.strftime("%B %Y"),
        income=income,
        spent=spent,
        savings_goal=goal,
        saved_so_far=income - spent,
        committed_remaining=committed,
        safe_to_spend=safe_to_spend,
        shortfall=shortfall,
        days_remaining=days_remaining,
        daily_allowance=daily_allowance,
        projected_expense=projected_expense,
        projected_savings=projected_savings,
        status=status,
        message=message,
        pending_recurring=pending,
    )


def category_budget_status(df: pd.DataFrame, budgets: dict[str, float],
                           as_of: date | pd.Timestamp | None = None) -> pd.DataFrame:
    """Return current-month utilization for every configured category budget."""
    columns = ["category", "limit", "spent", "remaining", "used_pct", "status"]
    if not budgets:
        return pd.DataFrame(columns=columns)

    as_of_ts = _as_timestamp(as_of)
    _, current = _current_rows(df, as_of_ts)
    expenses = current[current["type"] == "Expense"]
    totals = expenses.groupby("category")["amount"].sum() if not expenses.empty else pd.Series(dtype=float)

    rows = []
    for category, limit in sorted(budgets.items()):
        limit = max(0.0, float(limit))
        spent = float(totals.get(category, 0.0))
        used_pct = spent / limit * 100 if limit > 0 else 0.0
        if limit == 0:
            status = "No limit"
        elif spent > limit:
            status = "Over"
        elif used_pct >= 80:
            status = "Watch"
        else:
            status = "OK"
        rows.append({
            "category": category,
            "limit": limit,
            "spent": spent,
            "remaining": limit - spent,
            "used_pct": used_pct,
            "status": status,
        })
    return pd.DataFrame(rows, columns=columns)
