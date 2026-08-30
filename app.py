"""FinSight — intelligent personal finance dashboard.

Run with:
    streamlit run app.py
"""
from __future__ import annotations

from datetime import date

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src import anomaly, classifier, eda, insights, planner, prediction, recurring, ui
from src.database import (
    get_budgets, get_setting, init_db, insert_transaction, load_transactions,
    set_budget, set_setting,
)
from src.data_generator import generate
from src.preprocessing import add_features, clean, monthly_income_expense


st.set_page_config(
    page_title="FinSight — Finance Intelligence",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)
ui.inject_theme()
init_db()


def load_demo_data() -> int:
    from src.database import replace_transactions

    demo = generate()
    replace_transactions(demo)
    return len(demo)


def money_delta(current: float, previous: float) -> str | None:
    if previous == 0:
        return None
    difference = current - previous
    sign = "+" if difference >= 0 else "-"
    return f"{sign}₹{abs(difference):,.0f} vs prior month"


raw = load_transactions()

# --------------------------------------------------------------------------
# Sidebar — focused data controls
# --------------------------------------------------------------------------
with st.sidebar:
    ui.sidebar_brand()
    st.caption("Add, import, or generate data without leaving the dashboard.")

    with st.expander("＋ Add transaction", expanded=True):
        with st.form("add_tx", clear_on_submit=True):
            tx_date = st.date_input("Date", value=date.today())
            tx_type = st.selectbox("Type", ["Expense", "Income"])
            tx_amount = st.number_input("Amount (₹)", min_value=0.0, step=100.0)
            tx_category = st.text_input("Category", value="Food")
            tx_description = st.text_input("Description", placeholder="e.g. Team lunch")
            save_tx = st.form_submit_button("Save transaction", width="stretch")
            if save_tx:
                if tx_amount <= 0:
                    st.error("Enter an amount greater than zero.")
                elif not tx_category.strip():
                    st.error("Category cannot be empty.")
                else:
                    insert_transaction(
                        tx_date.isoformat(), float(tx_amount), tx_category.strip(),
                        tx_description.strip(), tx_type,
                    )
                    st.success("Transaction saved.")
                    st.rerun()

    with st.expander("⇧ Import CSV"):
        st.caption("Required columns: date, amount, category, description, type")
        upload = st.file_uploader("Choose a transaction file", type=["csv"], label_visibility="collapsed")
        import_csv = st.button("Import and replace", disabled=upload is None, width="stretch")
        if import_csv and upload is not None:
            try:
                imported = pd.read_csv(upload)
                required = {"date", "amount", "category", "description", "type"}
                missing = required.difference(imported.columns)
                if missing:
                    raise ValueError(f"Missing columns: {', '.join(sorted(missing))}")
                imported = clean(imported)
                if imported.empty:
                    raise ValueError("The file contains no valid transactions.")
                from src.database import replace_transactions

                replace_transactions(imported)
                st.success(f"Imported {len(imported):,} clean transactions.")
                st.rerun()
            except Exception as exc:
                st.error(f"Import failed: {exc}")

        template = pd.DataFrame(columns=["date", "amount", "category", "description", "type"])
        st.download_button(
            "Download CSV template", template.to_csv(index=False).encode("utf-8"),
            file_name="finsight_import_template.csv", mime="text/csv", width="stretch",
        )

    st.divider()
    st.markdown("##### Portfolio demo")
    st.caption("Generate nine months of realistic data to demonstrate every analytics module.")
    if st.button("Generate demo dataset", width="stretch"):
        count = load_demo_data()
        st.success(f"Loaded {count:,} transactions.")
        st.rerun()

    if not raw.empty:
        st.divider()
        st.caption(f"Database status  ·  {len(raw):,} records")
        st.markdown("<span class='meta-pill live'><span class='live-dot'></span>Local database connected</span>", unsafe_allow_html=True)

# --------------------------------------------------------------------------
# Empty state
# --------------------------------------------------------------------------
if raw.empty:
    ui.hero("No data", "No data", 0)
    st.markdown(
        """
        <div class="empty-card">
          <div class="empty-title">Your financial command center is ready.</div>
          <div class="empty-copy">Add a transaction, import a CSV, or load the portfolio demo to explore the complete experience.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Launch with demo data", type="primary"):
        load_demo_data()
        st.rerun()
    st.stop()

df = add_features(raw)
monthly_summary = monthly_income_expense(df)
latest = monthly_summary.iloc[-1]
previous = monthly_summary.iloc[-2] if len(monthly_summary) > 1 else None

# --------------------------------------------------------------------------
# Product hero and current-month executive snapshot
# --------------------------------------------------------------------------
ui.hero(
    df["date"].min().strftime("%b %Y"),
    df["date"].max().strftime("%b %Y"),
    len(df),
)

ui.section(
    "Executive snapshot",
    f"{pd.Period(latest['month_str'], freq='M').strftime('%B %Y')} performance",
    "Current-month results with comparison against the prior month.",
)

income = float(latest["income"])
expense = float(latest["expense"])
savings = float(latest["savings"])
savings_rate = (savings / income * 100) if income > 0 else 0.0
prior_income = float(previous["income"]) if previous is not None else 0.0
prior_expense = float(previous["expense"]) if previous is not None else 0.0
prior_savings = float(previous["savings"]) if previous is not None else 0.0
prior_rate = (prior_savings / prior_income * 100) if prior_income > 0 else 0.0

k1, k2, k3, k4 = st.columns(4)
k1.metric("Income", f"₹{income:,.0f}", money_delta(income, prior_income))
k2.metric(
    "Expenses", f"₹{expense:,.0f}", money_delta(expense, prior_expense),
    delta_color="inverse",
)
k3.metric("Net savings", f"₹{savings:,.0f}", money_delta(savings, prior_savings))
k4.metric(
    "Savings rate", f"{savings_rate:.1f}%",
    f"{savings_rate - prior_rate:+.1f} pts vs prior month" if previous is not None else None,
)

(
    overview_tab, planner_tab, insights_tab, forecast_tab,
    detection_tab, budgets_tab, transactions_tab,
) = st.tabs([
    "Overview", "Smart Plan", "Insights", "Forecast & Risk",
    "Detection", "Budgets", "Transactions",
])

# --------------------------------------------------------------------------
# Overview
# --------------------------------------------------------------------------
with overview_tab:
    ui.section(
        "Portfolio intelligence", "The complete financial picture",
        "Income, spending concentration, cash-flow movement, and behavioral patterns.",
    )
    daily = eda.daily_spend(df)
    category = eda.category_spend(df)

    chart_left, chart_right = st.columns([1.55, 1], gap="large")
    with chart_left:
        st.markdown("##### Income vs expense")
        monthly_chart = monthly_summary.melt(
            id_vars="month_str", value_vars=["income", "expense"],
            var_name="series", value_name="value",
        )
        monthly_fig = px.bar(
            monthly_chart, x="month_str", y="value", color="series", barmode="group",
            color_discrete_map={"income": ui.GREEN, "expense": ui.RED},
            labels={"value": "Amount (₹)", "month_str": "", "series": ""},
        )
        monthly_fig.update_traces(marker_line_width=0, hovertemplate="%{x}<br>₹%{y:,.0f}<extra></extra>")
        monthly_fig.update_layout(bargap=.28)
        st.plotly_chart(ui.style_figure(monthly_fig, 390), width="stretch", config={"displayModeBar": False})

    with chart_right:
        st.markdown("##### Spend concentration")
        category_fig = px.pie(
            category, names="category", values="amount", hole=.7,
            color_discrete_sequence=ui.CHART_COLORS,
        )
        category_fig.update_traces(
            textinfo="percent", textposition="inside",
            hovertemplate="%{label}<br>₹%{value:,.0f}<br>%{percent}<extra></extra>",
            marker={"line": {"color": "#0A1827", "width": 3}},
        )
        category_fig.update_layout(annotations=[{
            "text": f"₹{category['amount'].sum()/1000:,.0f}K<br><span style='font-size:11px;color:#94A3B8'>total spend</span>",
            "showarrow": False, "font": {"color": ui.INK, "size": 18},
        }])
        st.plotly_chart(ui.style_figure(category_fig, 390), width="stretch", config={"displayModeBar": False})

    st.markdown("##### Daily cash-flow movement")
    daily_fig = go.Figure(go.Scatter(
        x=daily["date"], y=daily["amount"], mode="lines",
        line={"color": ui.GREEN, "width": 2.4},
        fill="tozeroy", fillcolor="rgba(52,211,153,.07)",
        hovertemplate="%{x|%d %b %Y}<br>₹%{y:,.0f}<extra></extra>",
    ))
    st.plotly_chart(ui.style_figure(daily_fig, 310, legend=False), width="stretch", config={"displayModeBar": False})

    behavior_left, behavior_right = st.columns([1, 1.35], gap="large")
    with behavior_left:
        st.markdown("##### Spending rhythm")
        weekday = eda.weekday_pattern(df)
        weekday_fig = px.bar(
            weekday, x="day_of_week", y="amount", color="amount",
            color_continuous_scale=[[0, "#1B5260"], [1, ui.CYAN]],
            labels={"amount": "Average spend (₹)", "day_of_week": ""},
        )
        weekday_fig.update_layout(coloraxis_showscale=False)
        weekday_fig.update_traces(marker_line_width=0, hovertemplate="%{x}<br>₹%{y:,.0f}<extra></extra>")
        st.plotly_chart(ui.style_figure(weekday_fig, 310, legend=False), width="stretch", config={"displayModeBar": False})

    with behavior_right:
        st.markdown("##### Signals worth noticing")
        preview = insights.generate(df)[:4]
        for row_start in range(0, len(preview), 2):
            cards = st.columns(2)
            for offset, text in enumerate(preview[row_start:row_start + 2]):
                with cards[offset]:
                    ui.insight_card(row_start + offset + 1, text)

# --------------------------------------------------------------------------
# Smart Plan
# --------------------------------------------------------------------------
with planner_tab:
    ui.section(
        "Decision support", "Your safe-to-spend plan",
        "Savings are protected first, unpaid recurring bills are reserved next, and the remainder becomes your allowance.",
    )
    saved_goal = float(get_setting("monthly_savings_goal", "10000") or 0)
    plan = planner.build_monthly_plan(df, saved_goal)

    plan_left, plan_right = st.columns([1.55, 1], gap="large")
    with plan_left:
        ui.safe_spend_card(
            plan.safe_to_spend, plan.daily_allowance, plan.days_remaining,
            plan.status, plan.message,
        )
    with plan_right:
        with st.container(border=True):
            st.markdown("##### Savings target")
            st.caption("Set the amount you want the plan to protect every month.")
            with st.form("savings_goal_form"):
                goal = st.number_input(
                    "Monthly goal (₹)", min_value=0.0, step=500.0,
                    value=saved_goal,
                )
                if st.form_submit_button("Update plan", width="stretch"):
                    set_setting("monthly_savings_goal", goal)
                    st.success("Plan updated.")
                    st.rerun()
            st.metric("Goal protected", f"₹{plan.savings_goal:,.0f}")
            st.caption(f"Plan period · {plan.month}")

    plan_metrics = st.columns(4)
    plan_metrics[0].metric("Income this month", f"₹{plan.income:,.0f}")
    plan_metrics[1].metric("Spent so far", f"₹{plan.spent:,.0f}")
    plan_metrics[2].metric("Bills reserved", f"₹{plan.committed_remaining:,.0f}")
    plan_metrics[3].metric("Projected savings", f"₹{plan.projected_savings:,.0f}")

    if plan.savings_goal > 0 and plan.income > 0:
        protected = max(0.0, min(plan.savings_goal, plan.saved_so_far - plan.committed_remaining))
        st.caption(f"Goal coverage  ·  ₹{protected:,.0f} protected of ₹{plan.savings_goal:,.0f}")
        st.progress(min(1.0, protected / plan.savings_goal))

    pending_col, guardrail_col = st.columns([1, 1.35], gap="large")
    with pending_col:
        st.markdown("##### Commitments still reserved")
        if plan.pending_recurring.empty:
            st.success("All detected recurring commitments are covered.")
        else:
            pending_view = plan.pending_recurring.rename(columns={
                "description": "Bill", "category": "Category",
                "expected_amount": "Expected amount", "due_day": "Usual day",
                "due_status": "Status",
            })
            st.dataframe(
                pending_view, width="stretch", hide_index=True,
                column_config={
                    "Expected amount": st.column_config.NumberColumn(format="₹ %.0f"),
                },
            )

    with guardrail_col:
        st.markdown("##### Category guardrails")
        budget_status = planner.category_budget_status(df, get_budgets())
        if budget_status.empty:
            st.info("Set category budgets to activate guardrails.")
        else:
            budget_chart = budget_status.sort_values("used_pct")
            guardrail_fig = px.bar(
                budget_chart, x="used_pct", y="category", orientation="h",
                color="status",
                color_discrete_map={"OK": ui.GREEN, "Watch": ui.AMBER, "Over": ui.RED, "No limit": ui.MUTED},
                labels={"used_pct": "Budget used (%)", "category": "", "status": ""},
            )
            guardrail_fig.add_vline(x=100, line_dash="dot", line_color=ui.RED, opacity=.65)
            guardrail_fig.update_traces(hovertemplate="%{y}<br>%{x:.1f}% used<extra></extra>")
            st.plotly_chart(ui.style_figure(guardrail_fig, 300), width="stretch", config={"displayModeBar": False})

# --------------------------------------------------------------------------
# Insights
# --------------------------------------------------------------------------
with insights_tab:
    ui.section(
        "Behavioral analytics", "Signals translated into plain English",
        "The rule engine converts category, savings, timing, and trend patterns into concise decisions.",
    )
    generated_insights = insights.generate(df)
    for row_start in range(0, len(generated_insights), 3):
        insight_columns = st.columns(3)
        for offset, text in enumerate(generated_insights[row_start:row_start + 3]):
            with insight_columns[offset]:
                ui.insight_card(row_start + offset + 1, text)

    st.markdown("##### Behavioral split")
    weekend = eda.weekend_vs_weekday(df)
    b1, b2, b3 = st.columns(3)
    b1.metric("Average weekday spend", f"₹{weekend['weekday_avg']:,.0f}")
    b2.metric("Average weekend spend", f"₹{weekend['weekend_avg']:,.0f}")
    b3.metric(
        "Weekend uplift", f"{weekend['uplift_pct']:+.1f}%",
        delta_color="inverse" if weekend["uplift_pct"] > 0 else "normal",
    )

# --------------------------------------------------------------------------
# Forecast and risk
# --------------------------------------------------------------------------
with forecast_tab:
    ui.section(
        "Predictive layer", "Forward-looking expense intelligence",
        "A model forecast and overspending probability shown together for a complete risk view.",
    )
    forecast_result = prediction.forecast(df)
    risk_result = classifier.predict_overspend(df)
    forecast_col, risk_col = st.columns([1.5, 1], gap="large")

    with forecast_col:
        st.markdown("##### Next-month expense forecast")
        if forecast_result is None:
            st.info("At least four months of data are required for forecasting.")
        else:
            f1, f2, f3 = st.columns(3)
            f1.metric(f"Forecast · {forecast_result.next_month}", f"₹{forecast_result.predicted_expense:,.0f}")
            f2.metric("Selected model", forecast_result.model_used)
            f3.metric("Validation MAE", f"₹{forecast_result.mae:,.0f}")

            forecast_data = forecast_result.history.melt(
                id_vars="month_str", value_vars=["expense", "predicted"],
                var_name="series", value_name="amount",
            )
            forecast_fig = px.line(
                forecast_data, x="month_str", y="amount", color="series", markers=True,
                color_discrete_map={"expense": ui.GREEN, "predicted": ui.CYAN},
                labels={"month_str": "", "amount": "Amount (₹)", "series": ""},
            )
            forecast_fig.update_traces(line_width=2.5, marker_size=7, hovertemplate="%{x}<br>₹%{y:,.0f}<extra></extra>")
            st.plotly_chart(ui.style_figure(forecast_fig, 330), width="stretch", config={"displayModeBar": False})

    with risk_col:
        st.markdown("##### Overspend probability")
        if risk_result is None:
            st.info("At least four months of data are required for risk classification.")
        else:
            risk_pct = risk_result.probability * 100
            gauge_color = ui.RED if risk_pct >= 60 else ui.AMBER if risk_pct >= 35 else ui.GREEN
            gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=risk_pct,
                number={"suffix": "%", "font": {"color": ui.INK, "size": 42}},
                gauge={
                    "axis": {"range": [0, 100], "tickcolor": ui.MUTED, "tickfont": {"color": ui.MUTED}},
                    "bar": {"color": gauge_color, "thickness": .28},
                    "bgcolor": "rgba(148,163,184,.08)",
                    "borderwidth": 0,
                    "steps": [
                        {"range": [0, 35], "color": "rgba(52,211,153,.08)"},
                        {"range": [35, 60], "color": "rgba(251,191,36,.08)"},
                        {"range": [60, 100], "color": "rgba(251,113,133,.08)"},
                    ],
                },
            ))
            st.plotly_chart(ui.style_figure(gauge, 280, legend=False), width="stretch", config={"displayModeBar": False})
            st.markdown(f"**{risk_result.label}**")
            st.caption(risk_result.note)

    with st.expander("Model transparency"):
        st.markdown(
            "The expense forecast compares Linear Regression with a three-month Moving Average and selects the lower-error model. "
            "Overspend risk uses Logistic Regression when the historical labels contain enough variation; otherwise it reports a transparent rule-based fallback."
        )
        if forecast_result is not None:
            model_cols = st.columns(2)
            model_cols[0].metric("Forecast R²", f"{forecast_result.r2:.3f}" if forecast_result.r2 == forecast_result.r2 else "Not applicable")
            model_cols[1].metric("Forecast MAE", f"₹{forecast_result.mae:,.0f}")

# --------------------------------------------------------------------------
# Detection
# --------------------------------------------------------------------------
with detection_tab:
    ui.section(
        "Monitoring layer", "Anomalies and recurring commitments",
        "Statistical outliers surface unusual purchases while pattern mining identifies predictable monthly outflow.",
    )
    threshold = st.slider("Anomaly sensitivity · Z-score threshold", 1.5, 4.0, 2.5, 0.1)
    zscore_rows = anomaly.zscore_anomalies(df, threshold)
    iqr_rows = anomaly.iqr_anomalies_per_category(df)
    recurring_rows = recurring.detect(df)

    detect_metrics = st.columns(3)
    detect_metrics[0].metric("Global outliers", f"{len(zscore_rows)}")
    detect_metrics[1].metric("Category outliers", f"{len(iqr_rows)}")
    detect_metrics[2].metric(
        "Recurring monthly outflow",
        f"₹{recurring_rows['avg_amount'].sum():,.0f}" if not recurring_rows.empty else "₹0",
    )

    anomaly_col, recurring_col = st.columns([1.35, 1], gap="large")
    with anomaly_col:
        st.markdown("##### Unusual activity")
        if zscore_rows.empty and iqr_rows.empty:
            st.success("No unusual spending was detected at this sensitivity.")
        else:
            anomaly_view = pd.concat([
                zscore_rows.assign(method="Global Z-score"),
                iqr_rows.assign(method="Category IQR"),
            ], ignore_index=True).drop_duplicates(subset=["date", "amount", "category", "description"])
            st.dataframe(
                anomaly_view[["date", "amount", "category", "description", "method", "reason"]]
                    .sort_values("amount", ascending=False),
                width="stretch", hide_index=True,
                column_config={
                    "date": st.column_config.DateColumn("Date", format="DD MMM YYYY"),
                    "amount": st.column_config.NumberColumn("Amount", format="₹ %.0f"),
                },
            )

    with recurring_col:
        st.markdown("##### Recurring commitments")
        if recurring_rows.empty:
            st.info("No stable monthly patterns have been detected yet.")
        else:
            recurring_view = recurring_rows.rename(columns={
                "description": "Commitment", "category": "Category",
                "avg_amount": "Average amount", "occurrences": "Occurrences",
                "avg_interval_days": "Interval (days)",
            })
            st.dataframe(
                recurring_view, width="stretch", hide_index=True,
                column_config={
                    "Average amount": st.column_config.NumberColumn(format="₹ %.0f"),
                    "Interval (days)": st.column_config.NumberColumn(format="%.1f"),
                },
            )

# --------------------------------------------------------------------------
# Budgets
# --------------------------------------------------------------------------
with budgets_tab:
    ui.section(
        "Spending controls", "Category budget guardrails",
        "Define monthly limits and monitor utilization before a category becomes a problem.",
    )
    category_list = sorted(df.loc[df["type"] == "Expense", "category"].unique())
    budgets = get_budgets()

    budget_form_col, budget_view_col = st.columns([.75, 1.5], gap="large")
    with budget_form_col:
        with st.container(border=True):
            st.markdown("##### Set a monthly limit")
            with st.form("budget_form"):
                selected_category = st.selectbox("Category", category_list)
                monthly_limit = st.number_input(
                    "Limit (₹)", min_value=0.0, step=500.0,
                    value=float(budgets.get(selected_category, 0.0)),
                )
                if st.form_submit_button("Save budget", width="stretch"):
                    set_budget(selected_category, monthly_limit)
                    st.success("Budget saved.")
                    st.rerun()
            st.caption("A zero limit keeps the category visible without enforcing a ceiling.")

    with budget_view_col:
        budget_status = planner.category_budget_status(df, budgets)
        if budget_status.empty:
            st.info("No budgets yet. Set your first category limit to activate this view.")
        else:
            budget_plot = budget_status.sort_values("used_pct")
            budget_fig = px.bar(
                budget_plot, x="used_pct", y="category", orientation="h", color="status",
                color_discrete_map={"OK": ui.GREEN, "Watch": ui.AMBER, "Over": ui.RED, "No limit": ui.MUTED},
                labels={"used_pct": "Budget used (%)", "category": "", "status": ""},
            )
            budget_fig.add_vline(x=100, line_dash="dot", line_color=ui.RED, opacity=.7)
            budget_fig.update_traces(hovertemplate="%{y}<br>%{x:.1f}% used<extra></extra>")
            st.plotly_chart(ui.style_figure(budget_fig, 330), width="stretch", config={"displayModeBar": False})

    if budgets:
        status_table = planner.category_budget_status(df, budgets).rename(columns={
            "category": "Category", "limit": "Limit", "spent": "Spent",
            "remaining": "Remaining", "used_pct": "Used", "status": "Status",
        })
        status_table["Status"] = status_table["Status"].map({
            "OK": "● On track", "Watch": "● Watch", "Over": "● Over", "No limit": "● No limit",
        })
        st.dataframe(
            status_table, width="stretch", hide_index=True,
            column_config={
                "Limit": st.column_config.NumberColumn(format="₹ %.0f"),
                "Spent": st.column_config.NumberColumn(format="₹ %.0f"),
                "Remaining": st.column_config.NumberColumn(format="₹ %.0f"),
                "Used": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=max(100.0, float(status_table["Used"].max()))),
            },
        )

# --------------------------------------------------------------------------
# Transactions
# --------------------------------------------------------------------------
with transactions_tab:
    ui.section(
        "Data workspace", "Explore the transaction ledger",
        "Search, filter, inspect, and export the exact records powering every insight and model.",
    )
    with st.container(border=True):
        filter_cols = st.columns([1, 1.5, 1, 1])
        with filter_cols[0]:
            type_filter = st.selectbox("Type", ["All", "Expense", "Income"], key="ledger_type")
        with filter_cols[1]:
            category_filter = st.multiselect(
                "Categories", sorted(df["category"].unique()), placeholder="All categories",
            )
        with filter_cols[2]:
            start_date = st.date_input("From", value=df["date"].min().date(), key="ledger_start")
        with filter_cols[3]:
            end_date = st.date_input("To", value=df["date"].max().date(), key="ledger_end")
        search_term = st.text_input("Search descriptions", placeholder="Try rent, food, salary…")

    filtered = df[(df["date"].dt.date >= start_date) & (df["date"].dt.date <= end_date)].copy()
    if type_filter != "All":
        filtered = filtered[filtered["type"] == type_filter]
    if category_filter:
        filtered = filtered[filtered["category"].isin(category_filter)]
    if search_term.strip():
        filtered = filtered[
            filtered["description"].str.contains(search_term.strip(), case=False, na=False)
        ]

    ledger_metrics = st.columns(3)
    ledger_metrics[0].metric("Matching records", f"{len(filtered):,}")
    ledger_metrics[1].metric(
        "Filtered expense",
        f"₹{filtered.loc[filtered['type'] == 'Expense', 'amount'].sum():,.0f}",
    )
    ledger_metrics[2].metric(
        "Filtered income",
        f"₹{filtered.loc[filtered['type'] == 'Income', 'amount'].sum():,.0f}",
    )

    ledger_columns = ["date", "description", "category", "type", "amount"]
    st.dataframe(
        filtered[ledger_columns].sort_values("date", ascending=False),
        width="stretch", height=520, hide_index=True,
        column_config={
            "date": st.column_config.DateColumn("Date", format="DD MMM YYYY"),
            "description": st.column_config.TextColumn("Description", width="large"),
            "category": st.column_config.TextColumn("Category"),
            "type": st.column_config.TextColumn("Type"),
            "amount": st.column_config.NumberColumn("Amount", format="₹ %.2f"),
        },
    )
    st.download_button(
        "Download filtered CSV",
        filtered[ledger_columns].to_csv(index=False).encode("utf-8"),
        file_name="finsight_transactions.csv", mime="text/csv",
    )
