"""Executive Overview page."""

from __future__ import annotations

from pathlib import Path
import sys

import plotly.express as px
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from src.app_support.streamlit_helpers import apply_global_styles, format_currency, format_number, load_data, render_sidebar
from src.utils.snowflake_queries import fetch_executive_metrics, fetch_sales_trend, fetch_store_sales

st.set_page_config(page_title="Executive Overview", layout="wide")
apply_global_styles()
config = render_sidebar()

st.title("Executive Overview")
st.write("Live executive KPIs from Snowflake marts.")

metrics = load_data(fetch_executive_metrics, config)
trend = load_data(fetch_sales_trend, config)
store_sales = load_data(fetch_store_sales, config)

metric_values = metrics.iloc[0] if not metrics.empty else {}
metric_cols = st.columns(4)
metric_cols[0].metric("Total Sales", format_currency(metric_values.get("total_sales")))
metric_cols[1].metric("Stores", format_number(metric_values.get("store_count")))
metric_cols[2].metric("Departments", format_number(metric_values.get("dept_count")))
metric_cols[3].metric("High Risk Rows", format_number(metric_values.get("high_or_critical_risk_count")))

left, right = st.columns([1.2, 1])
with left:
    st.subheader("Sales Trend")
    if trend.empty:
        st.info("No sales trend data available yet.")
    else:
        fig = px.line(trend, x="sales_date", y="weekly_sales", markers=True)
        fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), yaxis_title="Weekly sales", xaxis_title=None)
        st.plotly_chart(fig, use_container_width=True)
with right:
    st.subheader("Store Performance")
    if store_sales.empty:
        st.info("No store sales data available yet.")
    else:
        fig = px.bar(store_sales, x="store_id", y="total_sales", color="store_type")
        fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), yaxis_title="Total sales", xaxis_title="Store")
        st.plotly_chart(fig, use_container_width=True)

st.subheader("Store Detail")
if store_sales.empty:
    st.info("Run dbt to populate mart tables.")
else:
    st.dataframe(store_sales, use_container_width=True, hide_index=True)
