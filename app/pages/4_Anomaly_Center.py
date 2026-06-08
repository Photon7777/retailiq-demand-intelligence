"""Anomaly Center page."""

from __future__ import annotations

from pathlib import Path
import sys

import plotly.express as px
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from src.app_support.streamlit_helpers import (
    apply_global_styles,
    configure_plotly_chart,
    load_data,
    render_empty_state,
    render_metric_cards,
    render_page_header,
    render_section_header,
    render_sidebar,
)
from src.utils.snowflake_queries import fetch_anomaly_results

st.set_page_config(page_title="Anomaly Center", layout="wide")
apply_global_styles()
config = render_sidebar()

render_page_header(
    "Anomaly Center",
    "Sales exception workbench",
    "Prioritized spike and drop detection for weekly sales patterns across stores and departments.",
    ["Spike detection", "Drop detection", "Severity triage"],
)

anomalies = load_data(fetch_anomaly_results, config)

render_section_header("Triage Filters", "Narrow the exception queue by severity and signal direction.")
with st.container(border=True):
    top_cols = st.columns(3)
    selected_severity = top_cols[0].selectbox("Severity", ["All", "High", "Medium", "Low"])
    selected_signal = top_cols[1].selectbox("Signal Type", ["All", "Sales spike", "Sales drop"])
    top_cols[2].selectbox("Time Window", ["Last 4 weeks", "Last 13 weeks", "Year to date"])

filtered = anomalies.copy()
if selected_severity != "All" and not filtered.empty:
    filtered = filtered[filtered["severity"] == selected_severity]
if selected_signal != "All" and not filtered.empty:
    filtered = filtered[filtered["direction"] == selected_signal]

if anomalies.empty:
    candidate_rows = "0"
    flagged_rows = "0"
    max_score = "0.00"
else:
    candidate_rows = f"{len(anomalies):,}"
    flagged_rows = f"{int(anomalies['is_anomaly'].sum()):,}"
    max_score = f"{anomalies['anomaly_score'].abs().max():.2f}"

render_metric_cards(
    [
        {"label": "Candidate Rows", "value": candidate_rows, "helper": "Rows reviewed", "tone": "blue"},
        {"label": "Flagged Anomalies", "value": flagged_rows, "helper": "Exceptions detected", "tone": "coral"},
        {"label": "Max Score", "value": max_score, "helper": "Largest absolute signal", "tone": "amber"},
        {"label": "Active Filter", "value": selected_severity, "helper": selected_signal, "tone": "teal"},
    ]
)

if not anomalies.empty:
    render_section_header("Anomaly Timeline", "Weekly sales values with severity and anomaly flags.")
    fig = px.scatter(
        anomalies,
        x="sales_date",
        y="weekly_sales",
        color="severity",
        symbol="is_anomaly",
        hover_data=["store_id", "dept_id", "anomaly_score"],
    )
    fig.update_layout(yaxis_title="Weekly sales", xaxis_title=None)
    configure_plotly_chart(fig, height=430)
    st.plotly_chart(fig, use_container_width=True)

render_section_header("Anomaly Queue", "Filtered list of candidate exceptions.")
if filtered.empty:
    render_empty_state("No matching anomalies", "No anomaly candidates match the current filters.")
else:
    st.dataframe(
        filtered[["sales_date", "store_id", "dept_id", "weekly_sales", "anomaly_score", "severity", "direction", "is_anomaly"]],
        use_container_width=True,
        hide_index=True,
    )
