"""Data Quality page."""

from __future__ import annotations

from pathlib import Path
import sys

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from src.app_support.streamlit_helpers import apply_global_styles, format_number, load_data, render_sidebar
from src.utils.snowflake_queries import fetch_platform_summary, fetch_quality_checks

st.set_page_config(page_title="Data Quality", layout="wide")
apply_global_styles()
config = render_sidebar()

st.title("Data Quality")
st.write("Operational checks over raw and mart objects in Snowflake.")

quality = load_data(fetch_quality_checks, config)
objects = load_data(fetch_platform_summary, config)

status_cols = st.columns(4)
raw_loaded = 0 if objects.empty else objects.query("table_schema == 'RAW' and row_count > 0")["table_name"].nunique()
mart_loaded = 0 if objects.empty else objects.query("table_schema == 'MARTS' and row_count > 0")["table_name"].nunique()
passing = 0 if quality.empty else (quality["status"] == "Pass").sum()
review = 0 if quality.empty else (quality["status"] != "Pass").sum()
status_cols[0].metric("Raw Tables Loaded", format_number(raw_loaded))
status_cols[1].metric("Mart Tables Loaded", format_number(mart_loaded))
status_cols[2].metric("Checks Passing", format_number(passing))
status_cols[3].metric("Open Reviews", format_number(review))

st.subheader("Quality Checks")
if quality.empty:
    st.info("No quality metadata available yet.")
else:
    st.dataframe(quality, use_container_width=True, hide_index=True)

st.subheader("Object Inventory")
if objects.empty:
    st.info("No Snowflake object metadata available yet.")
else:
    st.dataframe(objects, use_container_width=True, hide_index=True)
