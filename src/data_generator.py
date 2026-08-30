"""
Synthetic transaction generator.

Creates 9 months of realistic personal-finance data with:
  - monthly salary income
  - recurring bills (rent, internet, gym, streaming)
  - everyday expenses with weekend spikes
  - a small number of injected anomalies
The output is written to data/transactions.csv and loaded into SQLite.
"""

from __future__ import annotations

import os
import random
from datetime import date, timedelta

import numpy as np
import pandas as pd

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

CATEGORIES = {
    "Food":          {"mean": 300,  "std": 120, "freq_per_week": 5},
    "Transport":     {"mean": 150,  "std": 60,  "freq_per_week": 4},
    "Entertainment": {"mean": 500,  "std": 250, "freq_per_week": 1},
    "Shopping":      {"mean": 1200, "std": 800, "freq_per_week": 1},
    "Health":        {"mean": 600,  "std": 300, "freq_per_week": 0.3},
    "Education":     {"mean": 400,  "std": 200, "freq_per_week": 0.5},
    "Other":         {"mean": 250,  "std": 150, "freq_per_week": 1},
}

RECURRING = [
    {"description": "Rent",          "category": "Other",         "amount": 12000, "day": 1},
    {"description": "Internet bill", "category": "Other",         "amount": 999,   "day": 5},
    {"description": "Gym membership","category": "Health",        "amount": 1500,  "day": 7},
    {"description": "Netflix",       "category": "Entertainment", "amount": 499,   "day": 15},
    {"description": "Spotify",       "category": "Entertainment", "amount": 119,   "day": 20},
]

SALARY = 60000


def _random_expense(cat: str, when: date) -> dict:
    cfg = CATEGORIES[cat]
    weekend_boost = 1.4 if when.weekday() >= 5 else 1.0
    amount = max(20, np.random.normal(cfg["mean"], cfg["std"])) * weekend_boost
    return {
        "date": when,
        "amount": round(float(amount), 2),
        "category": cat,
        "description": f"{cat} expense",
        "type": "Expense",
    }


def generate(months: int = 9, out_path: str = "data/transactions.csv") -> pd.DataFrame:
    end = date.today().replace(day=28)
    start = (end - timedelta(days=months * 30)).replace(day=1)

    rows: list[dict] = []
    cur = start
    while cur <= end:
        # salary on the 1st
        if cur.day == 1:
            rows.append({
                "date": cur, "amount": SALARY, "category": "Salary",
                "description": "Monthly salary", "type": "Income",
            })
        # recurring
        for r in RECURRING:
            if cur.day == r["day"]:
                rows.append({
                    "date": cur, "amount": r["amount"], "category": r["category"],
                    "description": r["description"], "type": "Expense",
                })
        # daily expenses
        for cat, cfg in CATEGORIES.items():
            prob = cfg["freq_per_week"] / 7.0
            if random.random() < prob:
                rows.append(_random_expense(cat, cur))
        cur += timedelta(days=1)

    # Inject anomalies (large outliers) — useful for the anomaly module
    for _ in range(6):
        cat = random.choice(list(CATEGORIES.keys()))
        rand_day = start + timedelta(days=random.randint(0, (end - start).days))
        rows.append({
            "date": rand_day,
            "amount": round(CATEGORIES[cat]["mean"] * random.uniform(6, 12), 2),
            "category": cat,
            "description": f"Unusual {cat.lower()} purchase",
            "type": "Expense",
        })

    df = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    df.to_csv(out_path, index=False)
    return df


if __name__ == "__main__":
    from .database import init_db, replace_transactions

    df = generate()
    init_db()
    replace_transactions(df)
    print(f"Generated {len(df)} transactions → data/transactions.csv")
    print(df.head())
