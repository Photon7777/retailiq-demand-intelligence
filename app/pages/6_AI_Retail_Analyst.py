"""AI Retail Analyst page."""

from __future__ import annotations

import streamlit as st

from src.app_support.streamlit_helpers import apply_global_styles, format_currency, format_number, load_data, render_sidebar
from src.utils.snowflake_queries import fetch_demand_detail, fetch_executive_metrics, fetch_store_sales

st.set_page_config(page_title="AI Retail Analyst", layout="wide")
apply_global_styles()
config = render_sidebar()

st.title("AI Retail Analyst")
st.write("Phase 1.5 rule-based analyst preview over Snowflake marts.")

suggested = st.selectbox(
    "Suggested question",
    [
        "What are total sales?",
        "Which store has the highest sales?",
        "Which rows have the highest stockout risk?",
    ],
)
question = st.text_input("Business question", value=suggested)
if st.button("Ask Analyst", type="primary"):
    normalized = question.lower()
    if "total" in normalized and "sales" in normalized:
        metrics = load_data(fetch_executive_metrics, config)
        if metrics.empty:
            st.session_state["analyst_answer"] = "I could not load sales metrics from Snowflake yet."
        else:
            row = metrics.iloc[0]
            st.session_state["analyst_answer"] = (
                f"Total sales in the current mart sample are {format_currency(row.get('total_sales'))} "
                f"across {format_number(row.get('sales_records'))} sales records."
            )
        st.session_state["analyst_sql"] = "select sum(weekly_sales) from RETAILIQ_DB.MARTS.FACT_SALES;"
    elif "highest" in normalized and "sales" in normalized:
        stores = load_data(fetch_store_sales, config)
        if stores.empty:
            st.session_state["analyst_answer"] = "I could not load store sales from Snowflake yet."
        else:
            row = stores.iloc[0]
            st.session_state["analyst_answer"] = (
                f"Store {int(row['store_id'])} has the highest sales at {format_currency(row['total_sales'])}."
            )
        st.session_state["analyst_sql"] = "select store_id, sum(weekly_sales) from RETAILIQ_DB.MARTS.FACT_SALES group by 1;"
    else:
        risk = load_data(fetch_demand_detail, config)
        if risk.empty:
            st.session_state["analyst_answer"] = "I could not load stockout risk rows from Snowflake yet."
        else:
            top = risk.sort_values("stockout_risk_score", ascending=False).iloc[0]
            st.session_state["analyst_answer"] = (
                f"The highest stockout risk row is store {int(top['store_id'])}, department {int(top['dept_id'])}, "
                f"with a score of {top['stockout_risk_score']:.2f} and category {top['risk_category']}."
            )
        st.session_state["analyst_sql"] = "select * from RETAILIQ_DB.MARTS.FACT_DEMAND;"

st.subheader("Answer")
st.write(st.session_state.get("analyst_answer", "No response yet."))

st.subheader("Query Trace")
st.code(st.session_state.get("analyst_sql", "-- Query preview will appear after asking a question."), language="sql")
