"""AI Retail Analyst page."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from src.ai.retail_analyst_agent import AnalystResponse, answer_business_question  # noqa: E402
from src.app_support.streamlit_helpers import (  # noqa: E402
    apply_global_styles,
    render_empty_state,
    render_metric_cards,
    render_page_header,
    render_section_header,
    render_sidebar,
)

st.set_page_config(page_title="AI Retail Analyst", layout="wide")
apply_global_styles()
config = render_sidebar()

render_page_header(
    "AI Retail Analyst",
    "Governed business question workspace",
    "Ask plain-English retail questions, generate safe Snowflake SQL, and inspect the query trace behind every answer.",
    ["OpenAI-ready", "Read-only SQL", "MARTS governed", "Traceable answers"],
)

if "analyst_history" not in st.session_state:
    st.session_state["analyst_history"] = []

openai_ready = bool(config.openai_api_key)
render_metric_cards(
    [
        {
            "label": "Analyst Mode",
            "value": "OpenAI" if openai_ready else "Template",
            "helper": "LLM synthesis active" if openai_ready else "Add OPENAI_API_KEY to enable LLM mode",
            "tone": "lime" if openai_ready else "amber",
        },
        {"label": "SQL Scope", "value": "MARTS", "helper": "Approved tables only", "tone": "cobalt"},
        {"label": "Query Type", "value": "SELECT", "helper": "Read-only guardrails", "tone": "mint"},
        {
            "label": "History",
            "value": str(len(st.session_state["analyst_history"])),
            "helper": "Questions this session",
            "tone": "violet",
        },
    ]
)

question_col, guide_col = st.columns([1.25, 0.85])
with question_col:
    render_section_header("Ask RetailIQ", "Questions are translated into governed Snowflake SQL.")
    with st.container(border=True):
        suggested_question = st.selectbox(
            "Suggested question",
            [
                "What are total sales and how many stores are represented?",
                "Which stores have the highest sales?",
                "How accurate is the demand forecast?",
                "Which departments have the highest sales?",
                "Summarize stockout risk by category.",
                "Which rows have the highest stockout risk?",
                "Summarize sales anomalies by severity.",
            ],
        )
        question = st.text_area(
            "Business question",
            value=suggested_question,
            height=96,
            placeholder="Ask about sales, stores, forecast accuracy, stockout risk, or anomalies.",
        )
        controls = st.columns([1, 1])
        row_limit = controls[0].selectbox("Result row limit", [25, 50, 100, 250], index=2)
        ask = controls[1].button("Ask Analyst", type="primary", use_container_width=True)

with guide_col:
    render_section_header("Guardrails", "How the analyst keeps database access controlled.")
    st.markdown(
        """
        - Uses approved `MARTS` tables only
        - Blocks writes, DDL, account metadata, and multi-statement SQL
        - Adds result limits for detail queries
        - Shows generated SQL and result preview every time
        """
    )
    if openai_ready:
        st.success(f"OpenAI synthesis is configured with `{config.openai_model}`.")
    else:
        st.warning("OpenAI key is not configured yet. RetailIQ will use deterministic governed query templates.")

if ask:
    with st.spinner("Generating governed SQL and querying Snowflake..."):
        try:
            response = answer_business_question(question, config=config, row_limit=int(row_limit))
            st.session_state["analyst_history"].insert(0, response)
        except Exception as exc:  # noqa: BLE001 - keep the Streamlit app responsive
            st.error(f"The analyst could not answer this question: {exc}")

render_section_header("Conversation", "Latest answers with query traceability.")
if not st.session_state["analyst_history"]:
    render_empty_state(
        "No analyst questions yet",
        "Ask a question above to generate Snowflake SQL, execute it, and review the answer trace.",
    )

for index, item in enumerate(st.session_state["analyst_history"][:5], start=1):
    response: AnalystResponse = item
    with st.container(border=True):
        st.markdown(f"**Question {index}:** {response.question}")
        if response.warning:
            st.warning(response.warning)
        st.markdown(response.answer)
        trace_tab, data_tab = st.tabs(["SQL Trace", "Result Preview"])
        with trace_tab:
            st.caption(f"Rationale: {response.rationale}")
            st.code(response.sql, language="sql")
            st.caption(
                f"Rows returned: {response.row_count:,} | "
                f"Mode: {'OpenAI' if response.used_openai else 'Deterministic'} | "
                f"Model setting: {response.model or 'not configured'}"
            )
        with data_tab:
            if response.result_preview:
                st.dataframe(pd.DataFrame(response.result_preview), use_container_width=True, hide_index=True)
            else:
                render_empty_state("No rows returned", "The governed query executed but did not return result rows.")
