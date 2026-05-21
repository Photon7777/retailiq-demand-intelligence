"""RetailIQ Streamlit landing page."""

from __future__ import annotations

from pathlib import Path
import sys

import streamlit as st


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from src.utils.snowflake_connection import test_snowflake_connection  # noqa: E402


st.set_page_config(
    page_title="RetailIQ Demand Intelligence",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
    <style>
    .main .block-container {
        padding-top: 2rem;
        max-width: 1180px;
    }
    .metric-band {
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 1rem;
        background: #ffffff;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


with st.sidebar:
    st.title("RetailIQ")
    st.caption("Demand intelligence platform")
    st.divider()
    st.markdown("**Navigation**")
    st.write("Use the page menu to open forecast, risk, anomaly, quality, and AI analyst views.")
    st.divider()
    if st.button("Check Snowflake Connection", use_container_width=True):
        ok, message = test_snowflake_connection()
        if ok:
            st.success(message)
        else:
            st.warning(message)


st.title("RetailIQ: Cloud-Native Retail Demand Intelligence Platform")
st.write(
    "A Snowflake-backed retail analytics platform for demand forecasting, stockout risk monitoring, "
    "sales anomaly detection, and AI-assisted business analysis."
)

status_ok, status_message = test_snowflake_connection()
if status_ok:
    st.success(status_message)
else:
    st.info(status_message)

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
        `CSV / GCS` -> `Snowflake RAW` -> `dbt STAGING` -> `dbt MARTS` -> `ML outputs` -> `Streamlit + AI Analyst`
        """
    )
    st.info("Phase 1 includes the repository foundation and first local CSV-to-Snowflake ingestion path.")

st.subheader("Phase 1 Status")
status_cols = st.columns(4)
status_cols[0].metric("Raw Tables", "5", "Snowflake DDL")
status_cols[1].metric("dbt Layers", "3", "staging to marts")
status_cols[2].metric("App Pages", "6", "placeholders")
status_cols[3].metric("Tests", "3", "starter suite")

st.subheader("Next Build Areas")
next_cols = st.columns(3)
with next_cols[0]:
    st.markdown("**Demand Forecasting**")
    st.write("Train baseline models and persist predictions into Snowflake.")
with next_cols[1]:
    st.markdown("**Inventory Risk**")
    st.write("Generate synthetic inventory and rank stockout exposure.")
with next_cols[2]:
    st.markdown("**AI Analyst**")
    st.write("Answer business questions from governed Snowflake marts.")
