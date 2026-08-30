"""Rule-based natural-language insight engine."""
from __future__ import annotations

import pandas as pd

from . import eda
from .preprocessing import monthly_income_expense


def generate(df: pd.DataFrame) -> list[str]:
    out: list[str] = []
    if df.empty:
        return ["Add some transactions to start generating insights."]

    k = eda.kpis(df)
    cat = eda.category_spend(df)
    we = eda.weekend_vs_weekday(df)
    monthly = monthly_income_expense(df)

    # 1. expense / income ratio
    if k["income"] > 0:
        ratio = k["expense"] / k["income"] * 100
        out.append(f"💸 You spend **{ratio:.1f}%** of your income overall.")
        if ratio > 80:
            out.append("⚠️ Your spending exceeds 80% of income — savings buffer is thin.")
        elif ratio < 50:
            out.append("✅ Strong saver: you keep more than half of your income.")

    # 2. top category
    if not cat.empty:
        top = cat.iloc[0]
        out.append(
            f"🏆 Your highest expense category is **{top['category']}** "
            f"({top['share']*100:.1f}% of spending, ₹{top['amount']:,.0f})."
        )
        if len(cat) > 1:
            second = cat.iloc[1]
            out.append(
                f"🥈 Followed by **{second['category']}** at ₹{second['amount']:,.0f}."
            )

    # 3. category share warnings
    for _, row in cat.head(5).iterrows():
        if row["share"] > 0.35:
            out.append(
                f"📌 **{row['category']}** alone is {row['share']*100:.0f}% of expenses — "
                f"consider rebalancing."
            )

    # 4. weekend vs weekday
    if we["weekday_avg"] > 0:
        if we["uplift_pct"] > 15:
            out.append(
                f"📅 Weekend spending is **{we['uplift_pct']:.0f}% higher** than weekdays "
                f"(₹{we['weekend_avg']:,.0f} vs ₹{we['weekday_avg']:,.0f} per day)."
            )
        elif we["uplift_pct"] < -15:
            out.append(
                f"📅 You spend **{abs(we['uplift_pct']):.0f}% less** on weekends than weekdays."
            )

    # 5. monthly trend
    if len(monthly) >= 2:
        last, prev = monthly.iloc[-1], monthly.iloc[-2]
        if prev["expense"] > 0:
            change = (last["expense"] - prev["expense"]) / prev["expense"] * 100
            arrow = "📈" if change >= 0 else "📉"
            out.append(
                f"{arrow} Last month you spent ₹{last['expense']:,.0f}, "
                f"a {change:+.1f}% change vs the prior month."
            )

    # 6. savings rate
    if k["income"] > 0:
        out.append(f"🐷 Overall savings rate: **{k['savings_rate']*100:.1f}%**.")

    return out
