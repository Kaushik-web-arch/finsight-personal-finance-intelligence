"""Tiny SQLite layer — transactions, budgets, and app settings."""
from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager

import pandas as pd

DB_PATH = os.environ.get("FINANCE_DB", "data/finance.db")


@contextmanager
def get_conn():
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            type TEXT NOT NULL CHECK(type IN ('Income','Expense'))
        );
        CREATE TABLE IF NOT EXISTS budgets (
            category TEXT PRIMARY KEY,
            monthly_limit REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        """)


def replace_transactions(df: pd.DataFrame) -> None:
    init_db()
    with get_conn() as c:
        c.execute("DELETE FROM transactions")
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
        df[["date", "amount", "category", "description", "type"]].to_sql(
            "transactions", c, if_exists="append", index=False
        )


def insert_transaction(date: str, amount: float, category: str,
                       description: str, type_: str) -> None:
    init_db()
    with get_conn() as c:
        c.execute(
            "INSERT INTO transactions(date,amount,category,description,type) VALUES (?,?,?,?,?)",
            (date, amount, category, description, type_),
        )


def load_transactions() -> pd.DataFrame:
    init_db()
    with get_conn() as c:
        df = pd.read_sql("SELECT * FROM transactions", c, parse_dates=["date"])
    return df


def get_budgets() -> dict[str, float]:
    init_db()
    with get_conn() as c:
        rows = c.execute("SELECT category, monthly_limit FROM budgets").fetchall()
    return {cat: float(lim) for cat, lim in rows}


def set_budget(category: str, monthly_limit: float) -> None:
    init_db()
    with get_conn() as c:
        c.execute(
            "INSERT INTO budgets(category, monthly_limit) VALUES (?,?) "
            "ON CONFLICT(category) DO UPDATE SET monthly_limit=excluded.monthly_limit",
            (category, float(monthly_limit)),
        )


def get_setting(key: str, default: str = "") -> str:
    init_db()
    with get_conn() as c:
        row = c.execute("SELECT value FROM app_settings WHERE key = ?", (key,)).fetchone()
    return row[0] if row else default


def set_setting(key: str, value: str | float | int) -> None:
    init_db()
    with get_conn() as c:
        c.execute(
            "INSERT INTO app_settings(key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, str(value)),
        )
