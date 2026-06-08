"""AI Retail Analyst page."""

from __future__ import annotations

from pathlib import Path
import sys

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from src.app_support.streamlit_helpers import (
    apply_global_styles,
    format_currency,
    format_number,
    load_data,
    render_answer_panel,
    render_page_header,
    render_section_header,
    render_sidebar,
)
from src.utils.snowflake_queries import fetch_executive_metrics, fetch_stockout_risk_results, fetch_store_sales

st.set_page_config(page_title="AI Retail Analyst", layout="wide")
apply_global_styles()
config = render_sidebar()

render_page_header(
    "AI Retail Analyst",
    "Business question workspace",
    "A governed analyst interface that turns retail questions into Snowflake-backed answers and SQL traces.",
    ["Question answering", "SQL trace", "Snowflake marts"],
)

question_col, context_col = st.columns([1.2, 0.8])
with question_col:
    render_section_header("Ask A Question", "Use a governed question pattern backed by Snowflake marts.")
    with st.container(border=True):
        suggested = st.selectbox(
            "Suggested question",
            [
                "What are total sales?",
                "Which store has the highest sales?",
                "Which rows have the highest stockout risk?",
            ],
        )
        question = st.text_input("Business question", value=suggested)
        ask = st.button("Ask Analyst", type="primary", use_container_width=True)

with context_col:
    render_section_header("Analyst Context", "Current preview scope.")
    st.info("The Phase 3 build will connect this workspace to OpenAI-backed SQL generation with guardrails.")

if ask:
    with st.spinner("Querying Snowflake marts..."):
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
            risk = load_data(fetch_stockout_risk_results, config)
            if risk.empty:
                st.session_state["analyst_answer"] = "I could not load stockout risk rows from Snowflake yet."
            else:
                top = risk.sort_values("stockout_risk_score", ascending=False).iloc[0]
                st.session_state["analyst_answer"] = (
                    f"The highest stockout risk row is store {int(top['store_id'])}, department {int(top['dept_id'])}, "
                    f"with a score of {top['stockout_risk_score']:.2f} and category {top['risk_category']}."
                )
            st.session_state["analyst_sql"] = "select * from RETAILIQ_DB.MARTS.FACT_STOCKOUT_RISK;"

render_section_header("Answer", "Analyst response.")
render_answer_panel(st.session_state.get("analyst_answer", "No response yet."))

render_section_header("Query Trace", "SQL preview for transparency.")
st.code(st.session_state.get("analyst_sql", "-- Query preview will appear after asking a question."), language="sql")
