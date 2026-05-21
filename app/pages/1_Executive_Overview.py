"""Executive Overview page."""

from __future__ import annotations

import streamlit as st


st.set_page_config(page_title="Executive Overview", layout="wide")

st.title("Executive Overview")
st.write("A future command center for sales, forecast accuracy, stockout exposure, and anomaly trends.")

metric_cols = st.columns(4)
metric_cols[0].metric("Total Sales", "TBD")
metric_cols[1].metric("Forecast WAPE", "TBD")
metric_cols[2].metric("High Risk Items", "TBD")
metric_cols[3].metric("Anomalies", "TBD")

left, right = st.columns([1.2, 1])
with left:
    st.subheader("Sales Trend")
    st.line_chart({"weekly_sales": []})
with right:
    st.subheader("Top Attention Areas")
    st.dataframe(
        {"store": [], "department": [], "signal": [], "priority": []},
        use_container_width=True,
        hide_index=True,
    )

# TODO: Replace sample layout with Snowflake-backed KPI queries and Plotly visuals.
