# 📈 FinSight — Intelligent Personal Finance Tracker

[![Tests](https://github.com/Kaushik-web-arch/finsight-personal-finance-intelligence/actions/workflows/tests.yml/badge.svg)](https://github.com/Kaushik-web-arch/finsight-personal-finance-intelligence/actions/workflows/tests.yml)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.62+-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)

A local personal finance application with a Streamlit interface and an educational data-science pipeline.
It goes beyond CRUD: **data ingestion → feature engineering → EDA → decision support → forecasting → risk classification → anomaly detection**.

---

## 🖥️ Product preview

### Executive command center

A recruiter-facing overview of the product experience: live analytics status, monthly KPIs, savings performance, and navigation across the decision-support modules.

![FinSight executive finance dashboard](assets/screenshots/finsight-executive-dashboard.png)

### Spending intelligence

The analytics workspace combines income-versus-expense trends with category concentration and behavioral signals.

![FinSight spending analytics dashboard](assets/screenshots/finsight-spending-intelligence.png)

> Screenshots use synthetic portfolio data; no personal financial information is included.

---

## 🎯 What this project demonstrates

| Area | Technique |
|------|-----------|
| Data handling | pandas, SQLite, CSV ingestion |
| Preprocessing | missing values, dtype coercion, dedup, normalization |
| Feature engineering | `month`, `day_of_week`, `is_weekend`, rolling stats, `expense_ratio` |
| EDA | trend, category, behavioral pattern analysis |
| Insight engine | rule-based natural-language insight generation |
| ML — Regression | Linear regression and three-month moving-average forecast baselines |
| ML — Classification | Logistic Regression for overspend prediction |
| Anomaly detection | Z-score + IQR (per category) |
| Pattern mining | Recurring expense detection (amount + interval) |
| Decision support | Savings-goal-aware safe-to-spend planner |
| Product design | Responsive Executive Fintech UI and unified chart system |
| Dashboard | Streamlit + Plotly |

---

## 🏗️ Architecture

```
User Input / CSV ──► SQLite ──► Preprocessing ──► Feature Engineering
                                       │
                          ┌────────────┼────────────┐
                          ▼            ▼            ▼
                         EDA       Insights        ML
                          │            │            │
                          └──────► Streamlit Dashboard
```

---

## 📂 Project structure

```
finance_tracker/
├── app.py                       # Streamlit dashboard (entry point)
├── .streamlit/config.toml       # Executive Fintech theme configuration
├── requirements.txt
├── README.md
├── data/
│   └── transactions.csv         # synthetic dataset (auto-generated)
├── src/
│   ├── __init__.py
│   ├── data_generator.py        # synthetic transactions w/ realistic patterns
│   ├── database.py              # SQLite layer
│   ├── preprocessing.py         # cleaning + feature engineering
│   ├── eda.py                   # EDA aggregations
│   ├── insights.py              # rule-based insight engine
│   ├── prediction.py            # linear regression forecaster
│   ├── classifier.py            # overspend classifier
│   ├── anomaly.py               # Z-score + IQR anomaly detection
│   ├── recurring.py             # recurring expense detector
│   ├── planner.py               # savings goal + safe-to-spend plan
│   └── ui.py                    # visual system and Plotly styling
├── notebooks/
    └── analysis.ipynb           # full DS report (EDA + ML + evaluation)
└── tests/
    └── test_planner.py          # Smart Plan unit tests
```

---

## 🚀 Quick start

```bash
# 1. Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Generate synthetic data + initialize the database
python -m src.data_generator

# 4. Launch the dashboard
streamlit run app.py
```

The app opens at http://localhost:8501.

Run the automated Smart Plan checks with:

```bash
python -m unittest discover -s tests -v
```

---

## 📊 Dashboard features

- **Executive snapshot** — current income, expense, savings, and prior-month movement
- **Premium UI system** — responsive dark fintech styling, focused navigation, and consistent charts
- **Smart Plan** — set a savings goal and calculate a safe daily/monthly allowance
- **Bill reserve** — keeps detected but unpaid recurring bills out of spendable cash
- **Category guardrails** — live budget utilization with OK/watch/over status
- **Trends** — monthly + daily spending lines
- **Category breakdown** — pie + bar
- **Behavioral analysis** — weekend vs weekday, day-of-week heatmap
- **Budgets** — set per-category budget, see over-budget flags
- **🔍 Insights** — auto-generated natural-language statements
- **📈 Forecast** — next-month expense via linear regression or a three-month moving average
- **🚨 Anomalies** — unusually large transactions per category
- **🔄 Recurring** — auto-detected subscriptions / bills
- **🎯 Overspend classifier** — exploratory expense-versus-income risk signal
- **Filtered ledger** — search, filter, inspect, and export transaction subsets

---

## 🧪 Reproducing the DS report

Open `notebooks/analysis.ipynb` in Jupyter for the full academic write-up:
EDA charts, model evaluation (MAE, R², accuracy, confusion matrix), and discussion.

```bash
pip install jupyter
jupyter notebook notebooks/analysis.ipynb
```

---

## 🔬 Model scope and engineering decisions

- The included generator creates synthetic data so the public demo never exposes personal financial information.
- Forecasting compares interpretable baseline models rather than presenting a black-box model as artificial intelligence.
- Evaluation metrics are educational because the generated history is intentionally small; larger real-world datasets would require walk-forward validation and stronger holdout evaluation.
- SQLite keeps local setup simple. A multi-user production deployment should use authenticated users and a managed database such as PostgreSQL.
- The public portfolio version should use demo data or session-isolated uploads so one visitor cannot access another visitor's transactions.

---

## 🗣️ How to present this project

> *"I built FinSight, a decision-focused personal finance product that transforms raw transactions into behavioral insights, a safe-to-spend monthly plan, model-selected expense forecasts, overspending risk, and statistical anomaly alerts. I also designed a reusable Executive Fintech UI system in Streamlit and Plotly."*

---

## Evaluation boundaries

- [src/prediction.py](src/prediction.py) selects linear regression or a three-month moving average using MAE on one held-out final observation. This is a limited baseline comparison, not a multi-window walk-forward study.
- [src/classifier.py](src/classifier.py) reports training-set accuracy. It is not an unseen-data accuracy score. The target is expense exceeding income, not exceeding a user-defined category budget.
- The classifier's current-month wording and prediction features need alignment: inference uses the latest month's expense, rolling mean and expense ratio as prior context. Treat the output as an exploratory signal until the prediction horizon is specified and evaluated.
- [src/insights.py](src/insights.py) generates rule-based text; it does not call an LLM.
- [tests/test_planner.py](tests/test_planner.py) covers spending-plan calculations and category guardrails, not forecast or classifier accuracy.

### Reproducing evidence

Run the generator and test commands above in a disposable local installation. Record the commit, dependency versions, synthetic-data period and actual test result. Demonstrate how changing a savings goal changes the allowance, and how an unpaid recurring bill is reserved.

Before publishing ML performance claims, evaluate chronological holdout windows, report sample counts and compare against simple baselines. Keep synthetic-data results explicitly labeled; no real-world savings, forecasting-accuracy improvement or user adoption is established here.

## Copyright

© 2026 **Kaushik Santhosh**. All rights reserved.

This repository and its source code are provided publicly for portfolio, educational review, and demonstration purposes. No permission is granted to copy, modify, redistribute, sublicense, or use substantial portions of this project without prior written permission from the copyright holder.
