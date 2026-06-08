"""Data Quality page."""

from __future__ import annotations

from pathlib import Path
import sys

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from src.app_support.streamlit_helpers import (
    apply_global_styles,
    format_number,
    load_data,
    render_empty_state,
    render_metric_cards,
    render_page_header,
    render_section_header,
    render_sidebar,
)
from src.utils.snowflake_queries import fetch_platform_summary, fetch_quality_checks

st.set_page_config(page_title="Data Quality", layout="wide")
apply_global_styles()
config = render_sidebar()

render_page_header(
    "Data Quality",
    "Warehouse observability",
    "Object inventory and quality checks for the raw, staging, mart, and ML layers.",
    ["Table health", "dbt tests", "Object inventory"],
)

quality = load_data(fetch_quality_checks, config)
objects = load_data(fetch_platform_summary, config)

raw_loaded = 0 if objects.empty else objects.query("table_schema == 'RAW' and row_count > 0")["table_name"].nunique()
mart_loaded = 0 if objects.empty else objects.query("table_schema == 'MARTS' and row_count > 0")["table_name"].nunique()
passing = 0 if quality.empty else (quality["status"] == "Pass").sum()
review = 0 if quality.empty else (quality["status"] != "Pass").sum()
render_metric_cards(
    [
        {"label": "Raw Tables Loaded", "value": format_number(raw_loaded), "helper": "Source coverage", "tone": "blue"},
        {"label": "Mart Tables Loaded", "value": format_number(mart_loaded), "helper": "Analytics coverage", "tone": "teal"},
        {"label": "Checks Passing", "value": format_number(passing), "helper": "Current quality status", "tone": "green"},
        {"label": "Open Reviews", "value": format_number(review), "helper": "Items needing attention", "tone": "amber"},
    ]
)

render_section_header("Quality Checks", "Rule-level data quality status.")
if quality.empty:
    render_empty_state("No quality metadata", "Quality checks will appear once mart metadata is available.")
else:
    st.dataframe(quality, use_container_width=True, hide_index=True)

render_section_header("Object Inventory", "Snowflake objects available to the app.")
if objects.empty:
    render_empty_state("No object inventory", "No Snowflake object metadata is available yet.")
else:
    st.dataframe(objects, use_container_width=True, hide_index=True)
