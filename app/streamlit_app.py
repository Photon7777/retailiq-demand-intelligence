"""RetailIQ Streamlit landing page."""

from __future__ import annotations

from pathlib import Path
import sys

import streamlit as st


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from src.app_support.streamlit_helpers import (  # noqa: E402
    apply_global_styles,
    format_currency,
    format_number,
    load_data,
    render_sidebar,
)
from src.utils.snowflake_queries import fetch_executive_metrics, fetch_platform_summary  # noqa: E402


st.set_page_config(
    page_title="RetailIQ Demand Intelligence",
    layout="wide",
    initial_sidebar_state="expanded",
)


apply_global_styles()
config = render_sidebar()


st.title("RetailIQ: Cloud-Native Retail Demand Intelligence Platform")
st.write(
    "A Snowflake-backed retail analytics platform for demand forecasting, stockout risk monitoring, "
    "sales anomaly detection, and AI-assisted business analysis."
)

metrics = load_data(fetch_executive_metrics, config)
platform_summary = load_data(fetch_platform_summary, config)

if st.session_state.get("snowflake_status", {}).get("ok"):
    st.success(st.session_state["snowflake_status"]["message"])
else:
    st.info("Use the sidebar MFA field to check Snowflake and refresh live dashboard data.")

overview_col, architecture_col = st.columns([1.1, 1])

with overview_col:
    st.subheader("Project Overview")
    st.write(
        "RetailIQ ingests raw retail data, transforms it into analytics-ready tables, generates demand "
        "signals, and serves operational insights through Streamlit and an AI analyst interface."
    )
    st.markdown(
        """
        - Raw Walmart sales, store, feature, weather, and inventory files
        - Snowflake schemas for raw, staging, marts, ML, and analytics layers
        - dbt transformations for governed analytics models
        - Python ML workflows for forecasts, risk scores, and anomaly flags
        - Streamlit app for executive and operator workflows
        """
    )

with architecture_col:
    st.subheader("Architecture Summary")
    st.markdown(
        """
        `CSV / GCS` -> `Snowflake RAW` -> `dbt STAGING` -> `dbt MARTS` -> `Snowflake ML` -> `Streamlit + AI Analyst`
        """
    )
    st.info("Phase 2 adds canonical Walmart prep, baseline ML outputs, and Snowflake-backed model marts.")

st.subheader("Pipeline Status")
status_cols = st.columns(4)
if not platform_summary.empty:
    raw_count = platform_summary.query("table_schema == 'RAW'")["table_name"].nunique()
    mart_count = platform_summary.query("table_schema == 'MARTS'")["table_name"].nunique()
    ml_count = platform_summary.query("table_schema == 'ML'")["table_name"].nunique()
    status_cols[0].metric("Raw Tables", format_number(raw_count))
    status_cols[1].metric("Mart Tables", format_number(mart_count))
    status_cols[2].metric("ML Tables", format_number(ml_count))
else:
    status_cols[0].metric("Raw Tables", "5")
    status_cols[1].metric("Mart Tables", "5")
    status_cols[2].metric("ML Tables", "3")

if not metrics.empty:
    first_row = metrics.iloc[0]
    status_cols[3].metric("Total Sales", format_currency(first_row.get("total_sales")))
else:
    status_cols[3].metric("Total Sales", "$0")

st.subheader("Warehouse Objects")
if platform_summary.empty:
    st.info("Run the sample ingestion and dbt commands to populate live object metadata.")
else:
    st.dataframe(
        platform_summary[["table_schema", "table_name", "table_type", "row_count", "last_altered"]],
        use_container_width=True,
        hide_index=True,
    )

st.subheader("Next Build Areas")
next_cols = st.columns(3)
with next_cols[0]:
    st.markdown("**Forecasting Model**")
    st.write("Evaluate the baseline model against the full Walmart history and add richer lag features.")
with next_cols[1]:
    st.markdown("**Inventory Simulation**")
    st.write("Tune synthetic inventory assumptions for service-level and reorder-point scenarios.")
with next_cols[2]:
    st.markdown("**AI Analyst**")
    st.write("Connect OpenAI-backed SQL generation to the governed mart layer.")
