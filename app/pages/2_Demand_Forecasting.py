"""Demand Forecasting page."""

from __future__ import annotations

import streamlit as st


st.set_page_config(page_title="Demand Forecasting", layout="wide")

st.title("Demand Forecasting")
st.write("Forecast demand by store, department, and week once Phase 2 model outputs are available.")

filter_cols = st.columns(3)
filter_cols[0].selectbox("Store", ["All stores"])
filter_cols[1].selectbox("Department", ["All departments"])
filter_cols[2].selectbox("Forecast Horizon", ["4 weeks", "8 weeks", "12 weeks"])

chart_col, table_col = st.columns([1.3, 1])
with chart_col:
    st.subheader("Actual vs Forecast")
    st.line_chart({"actual_sales": [], "forecast_sales": []})
with table_col:
    st.subheader("Forecast Detail")
    st.dataframe(
        {"date": [], "store": [], "department": [], "forecast": [], "confidence": []},
        use_container_width=True,
        hide_index=True,
    )

# TODO: Load forecast outputs from Snowflake ML or ANALYTICS schema.
