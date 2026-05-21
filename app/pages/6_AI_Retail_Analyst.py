"""AI Retail Analyst page."""

from __future__ import annotations

import streamlit as st


st.set_page_config(page_title="AI Retail Analyst", layout="wide")

st.title("AI Retail Analyst")
st.write("Ask governed business questions over Snowflake-backed RetailIQ data in natural language.")

question = st.text_input("Business question", placeholder="Which stores have the highest stockout risk next week?")
if st.button("Ask Analyst", type="primary"):
    st.info("The AI analyst will be connected after governed mart tables are available.")

st.subheader("Answer")
st.write("No response yet.")

st.subheader("Query Trace")
st.code("-- Generated SQL preview will appear here in a later phase.", language="sql")

# TODO: Add OpenAI SQL generation, Snowflake execution, guardrails, and answer synthesis.
