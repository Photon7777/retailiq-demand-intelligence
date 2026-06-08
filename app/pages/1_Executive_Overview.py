"""Executive Overview page."""

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
    format_compact_currency,
    format_number,
    load_data,
    render_empty_state,
    render_metric_cards,
    render_page_header,
    render_section_header,
    render_sidebar,
)
from src.utils.snowflake_queries import fetch_executive_metrics, fetch_sales_trend, fetch_store_sales

st.set_page_config(page_title="Executive Overview", layout="wide")
apply_global_styles()
config = render_sidebar()

render_page_header(
    "Executive Overview",
    "Retail performance cockpit",
    "Top-line sales, store coverage, and demand-risk signals from the governed Snowflake mart layer.",
    ["Live marts", "Store performance", "Sales trend"],
)

metrics = load_data(fetch_executive_metrics, config)
trend = load_data(fetch_sales_trend, config)
store_sales = load_data(fetch_store_sales, config)

metric_values = metrics.iloc[0] if not metrics.empty else {}
render_metric_cards(
    [
        {"label": "Total Sales", "value": format_compact_currency(metric_values.get("total_sales")), "helper": "All mart sales", "tone": "teal"},
        {"label": "Stores", "value": format_number(metric_values.get("store_count")), "helper": "Active locations", "tone": "blue"},
        {"label": "Departments", "value": format_number(metric_values.get("dept_count")), "helper": "Merchandising groups", "tone": "green"},
        {
            "label": "High Risk Rows",
            "value": format_number(metric_values.get("high_or_critical_risk_count")),
            "helper": "Risk score above 0.90",
            "tone": "coral",
        },
    ]
)

left, right = st.columns([1.2, 1])
with left:
    render_section_header("Sales Trend", "Weekly revenue movement across all loaded stores.")
    if trend.empty:
        render_empty_state("No sales trend", "Run dbt to populate the sales mart.")
    else:
        fig = px.line(trend, x="sales_date", y="weekly_sales", markers=True)
        fig.update_layout(yaxis_title="Weekly sales", xaxis_title=None)
        configure_plotly_chart(fig, height=372)
        st.plotly_chart(fig, use_container_width=True)
with right:
    render_section_header("Store Performance", "Total sales by store and format.")
    if store_sales.empty:
        render_empty_state("No store sales", "Store performance appears after mart tables are available.")
    else:
        fig = px.bar(store_sales, x="store_id", y="total_sales", color="store_type")
        fig.update_layout(yaxis_title="Total sales", xaxis_title="Store")
        configure_plotly_chart(fig, height=372)
        st.plotly_chart(fig, use_container_width=True)

render_section_header("Store Detail", "Store-level sales table for drilldown.")
if store_sales.empty:
    render_empty_state("No store detail", "Run dbt to populate mart tables.")
else:
    st.dataframe(store_sales, use_container_width=True, hide_index=True)
