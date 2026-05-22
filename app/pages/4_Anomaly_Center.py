"""Anomaly Center page."""

from __future__ import annotations

from pathlib import Path
import sys

import plotly.express as px
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from src.app_support.streamlit_helpers import apply_global_styles, load_data, render_sidebar
from src.utils.snowflake_queries import fetch_anomaly_results

st.set_page_config(page_title="Anomaly Center", layout="wide")
apply_global_styles()
config = render_sidebar()

st.title("Anomaly Center")
st.write("Sales anomaly results from the Phase 2 ML output mart, with a z-score fallback before ML outputs are loaded.")

anomalies = load_data(fetch_anomaly_results, config)

top_cols = st.columns(3)
selected_severity = top_cols[0].selectbox("Severity", ["All", "High", "Medium", "Low"])
selected_signal = top_cols[1].selectbox("Signal Type", ["All", "Sales spike", "Sales drop"])
top_cols[2].selectbox("Time Window", ["Last 4 weeks", "Last 13 weeks", "Year to date"])

filtered = anomalies.copy()
if selected_severity != "All" and not filtered.empty:
    filtered = filtered[filtered["severity"] == selected_severity]
if selected_signal != "All" and not filtered.empty:
    filtered = filtered[filtered["direction"] == selected_signal]

metric_cols = st.columns(3)
if anomalies.empty:
    metric_cols[0].metric("Candidate Rows", "0")
    metric_cols[1].metric("Flagged Anomalies", "0")
    metric_cols[2].metric("Max Score", "0.00")
else:
    metric_cols[0].metric("Candidate Rows", f"{len(anomalies):,}")
    metric_cols[1].metric("Flagged Anomalies", f"{int(anomalies['is_anomaly'].sum()):,}")
    metric_cols[2].metric("Max Score", f"{anomalies['anomaly_score'].abs().max():.2f}")

if not anomalies.empty:
    fig = px.scatter(
        anomalies,
        x="sales_date",
        y="weekly_sales",
        color="severity",
        symbol="is_anomaly",
        hover_data=["store_id", "dept_id", "anomaly_score"],
    )
    fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), yaxis_title="Weekly sales", xaxis_title=None)
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Anomaly Queue")
if filtered.empty:
    st.info("No anomaly candidates match the current filters.")
else:
    st.dataframe(
        filtered[["sales_date", "store_id", "dept_id", "weekly_sales", "anomaly_score", "severity", "direction", "is_anomaly"]],
        use_container_width=True,
        hide_index=True,
    )
