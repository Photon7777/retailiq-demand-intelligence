"""Data Quality page."""

from __future__ import annotations

import streamlit as st


st.set_page_config(page_title="Data Quality", layout="wide")

st.title("Data Quality")
st.write("Monitor source freshness, row counts, null checks, key uniqueness, and dbt test results.")

status_cols = st.columns(4)
status_cols[0].metric("Raw Tables Loaded", "TBD")
status_cols[1].metric("dbt Tests Passing", "TBD")
status_cols[2].metric("Freshness Checks", "TBD")
status_cols[3].metric("Open Issues", "TBD")

st.subheader("Quality Checks")
st.dataframe(
    {"check_name": [], "table_name": [], "status": [], "last_run_at": []},
    use_container_width=True,
    hide_index=True,
)

# TODO: Surface dbt artifacts, source freshness, and custom data quality checks.
