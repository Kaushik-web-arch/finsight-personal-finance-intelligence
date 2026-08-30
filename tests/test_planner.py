from datetime import date
import unittest

import pandas as pd

from src.planner import build_monthly_plan, category_budget_status


def sample_transactions(include_current_rent: bool = False) -> pd.DataFrame:
    rows = [
        ["2026-06-01", 10000, "Housing", "Rent", "Expense"],
        ["2026-07-01", 10000, "Housing", "Rent", "Expense"],
        ["2026-08-01", 60000, "Salary", "Salary", "Income"],
        ["2026-08-05", 500, "Food", "Lunch", "Expense"],
    ]
    if include_current_rent:
        rows.append(["2026-08-01", 10000, "Housing", "Rent", "Expense"])
    return pd.DataFrame(rows, columns=["date", "amount", "category", "description", "type"])


class PlannerTests(unittest.TestCase):
    def test_plan_reserves_unpaid_recurring_bill(self):
        plan = build_monthly_plan(
            sample_transactions(), savings_goal=20000, as_of=date(2026, 8, 10)
        )

        self.assertEqual(plan.committed_remaining, 10000)
        self.assertEqual(plan.safe_to_spend, 29500)
        self.assertAlmostEqual(plan.daily_allowance, 29500 / 22)
        self.assertEqual(plan.status, "On track")
        self.assertEqual(plan.pending_recurring.iloc[0]["description"], "Rent")

    def test_paid_recurring_bill_is_not_reserved_twice(self):
        plan = build_monthly_plan(
            sample_transactions(include_current_rent=True),
            savings_goal=20000,
            as_of=date(2026, 8, 10),
        )

        self.assertEqual(plan.committed_remaining, 0)
        self.assertEqual(plan.safe_to_spend, 29500)
        self.assertTrue(plan.pending_recurring.empty)

    def test_plan_reports_goal_that_exceeds_income(self):
        plan = build_monthly_plan(
            sample_transactions(), savings_goal=70000, as_of=date(2026, 8, 10)
        )

        self.assertEqual(plan.safe_to_spend, 0)
        self.assertEqual(plan.shortfall, 20500)
        self.assertEqual(plan.status, "Goal too high")

    def test_category_budget_guardrails(self):
        result = category_budget_status(
            sample_transactions(), {"Food": 550, "Housing": 9000}, date(2026, 8, 10)
        ).set_index("category")

        self.assertEqual(result.loc["Food", "status"], "Watch")
        self.assertEqual(result.loc["Housing", "status"], "OK")


if __name__ == "__main__":
    unittest.main()
