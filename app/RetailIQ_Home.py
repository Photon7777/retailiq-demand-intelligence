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
    format_compact_currency,
    format_number,
    render_empty_state,
    render_action_cards,
    render_metric_cards,
    render_page_header,
    render_pipeline_rail,
    render_section_header,
    render_status_grid,
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


render_page_header(
    "RetailIQ",
    "Retail operations intelligence",
    "A Snowflake-backed retail command center for forecasting demand, spotting stockout exposure, detecting anomalies, and turning governed marts into executive answers.",
    ["Snowflake warehouse", "dbt mart layer", "Forecast model", "Cloud Run live demo"],
)

metrics = load_data(fetch_executive_metrics, config)
platform_summary = load_data(fetch_platform_summary, config)

if st.session_state.get("snowflake_status", {}).get("ok"):
    st.success(st.session_state["snowflake_status"]["message"])
else:
    st.info("Use the sidebar connection check to validate Snowflake and refresh dashboard data.")

raw_count = 0 if platform_summary.empty else platform_summary.query("table_schema == 'RAW'")["table_name"].nunique()
mart_count = 0 if platform_summary.empty else platform_summary.query("table_schema == 'MARTS'")["table_name"].nunique()
ml_count = 0 if platform_summary.empty else platform_summary.query("table_schema == 'ML'")["table_name"].nunique()
metric_values = metrics.iloc[0] if not metrics.empty else {}

render_metric_cards(
    [
        {"label": "Total Sales", "value": format_compact_currency(metric_values.get("total_sales")), "helper": "Mart-backed sales", "tone": "teal"},
        {"label": "Raw Tables", "value": format_number(raw_count or 5), "helper": "Source layer", "tone": "blue"},
        {"label": "Mart Tables", "value": format_number(mart_count or 5), "helper": "Analytics layer", "tone": "green"},
        {"label": "ML Tables", "value": format_number(ml_count or 3), "helper": "Forecast, risk, anomalies", "tone": "amber"},
    ]
)

render_status_grid(
    [
        ("Runtime", "Cloud Run"),
        ("Warehouse", "Snowflake"),
        ("Transform", "dbt marts"),
        ("Interface", "Streamlit"),
    ]
)

overview_col, architecture_col = st.columns([1.05, 1])

with overview_col:
    render_section_header("Project Overview", "Pipeline layers and operational workflows.")
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
    render_section_header("Architecture Summary", "Cloud-native path from raw files to decisions.")
    render_pipeline_rail(
        [
            ("Retail CSV", "Walmart sales, stores, features, weather, and inventory"),
            ("Snowflake RAW", "Auditable landing tables for source data"),
            ("dbt STAGING", "Typed, cleaned, analytics-safe views"),
            ("dbt MARTS", "Sales, inventory, demand, forecast, and risk facts"),
            ("ML Outputs", "Forecast, anomaly, and stockout scoring tables"),
            ("Streamlit", "Live business workflow and AI analyst interface"),
        ]
    )
    st.info("Phase 2 adds Walmart prep, baseline ML outputs, and Snowflake-backed model marts.")

render_section_header("Warehouse Objects", "Live object inventory from Snowflake.")
if platform_summary.empty:
    render_empty_state("No object metadata", "Snowflake objects will appear here after the warehouse connection is available.")
else:
    st.dataframe(
        platform_summary[["table_schema", "table_name", "table_type", "row_count", "last_altered"]],
        use_container_width=True,
        hide_index=True,
    )

render_section_header("Next Build Areas", "Upcoming product increments.")
render_action_cards(
    [
        ("Forecasting Model", "Evaluate the baseline model against the full Walmart history and add richer lag, holiday, and store-format features."),
        ("Inventory Simulation", "Tune synthetic inventory assumptions for service-level, reorder-point, and recovery-time scenarios."),
        ("AI Analyst", "Connect OpenAI-backed SQL generation to the governed mart layer with guardrails and query traceability."),
    ]
)
