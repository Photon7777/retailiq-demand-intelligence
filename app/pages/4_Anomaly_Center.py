"""Anomaly Center page."""

from __future__ import annotations

import streamlit as st


st.set_page_config(page_title="Anomaly Center", layout="wide")

st.title("Anomaly Center")
st.write("Investigate unusual sales movement by store, department, week, and external conditions.")

top_cols = st.columns(3)
top_cols[0].selectbox("Severity", ["All", "High", "Medium", "Low"])
top_cols[1].selectbox("Signal Type", ["All", "Sales spike", "Sales drop"])
top_cols[2].selectbox("Time Window", ["Last 4 weeks", "Last 13 weeks", "Year to date"])

st.subheader("Anomaly Queue")
st.dataframe(
    {
        "date": [],
        "store": [],
        "department": [],
        "weekly_sales": [],
        "anomaly_score": [],
        "status": [],
    },
    use_container_width=True,
    hide_index=True,
)

# TODO: Add anomaly detection outputs and reviewer workflow states.
