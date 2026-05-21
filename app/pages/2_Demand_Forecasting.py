"""Demand Forecasting page."""

from __future__ import annotations

import plotly.express as px
import streamlit as st

from src.app_support.streamlit_helpers import apply_global_styles, format_currency, load_data, render_sidebar
from src.utils.snowflake_queries import fetch_baseline_forecast

st.set_page_config(page_title="Demand Forecasting", layout="wide")
apply_global_styles()
config = render_sidebar()

st.title("Demand Forecasting")
st.write("Phase 1.5 baseline forecast using the previous observation or segment average as a simple benchmark.")

forecast = load_data(fetch_baseline_forecast, config)

filter_cols = st.columns(3)
store_options = ["All stores"] + sorted(forecast["store_id"].dropna().astype(int).unique().tolist()) if not forecast.empty else ["All stores"]
dept_options = (
    ["All departments"] + sorted(forecast["dept_id"].dropna().astype(int).unique().tolist()) if not forecast.empty else ["All departments"]
)
selected_store = filter_cols[0].selectbox("Store", store_options)
selected_dept = filter_cols[1].selectbox("Department", dept_options)
filter_cols[2].selectbox("Forecast Horizon", ["Baseline only"])

filtered = forecast.copy()
if selected_store != "All stores" and not filtered.empty:
    filtered = filtered[filtered["store_id"] == selected_store]
if selected_dept != "All departments" and not filtered.empty:
    filtered = filtered[filtered["dept_id"] == selected_dept]

if not filtered.empty:
    wape = filtered["absolute_error"].sum() / filtered["weekly_sales"].abs().sum()
    metric_cols = st.columns(3)
    metric_cols[0].metric("Observed Sales", format_currency(filtered["weekly_sales"].sum()))
    metric_cols[1].metric("Baseline WAPE", f"{wape:.1%}")
    metric_cols[2].metric("Records", f"{len(filtered):,}")

chart_col, table_col = st.columns([1.3, 1])
with chart_col:
    st.subheader("Actual vs Baseline")
    if filtered.empty:
        st.info("No forecast baseline data available yet.")
    else:
        chart_df = filtered.melt(
            id_vars=["sales_date", "store_id", "dept_id"],
            value_vars=["weekly_sales", "baseline_forecast"],
            var_name="series",
            value_name="sales",
        )
        fig = px.line(chart_df, x="sales_date", y="sales", color="series", markers=True)
        fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), yaxis_title="Sales", xaxis_title=None)
        st.plotly_chart(fig, use_container_width=True)
with table_col:
    st.subheader("Forecast Detail")
    if filtered.empty:
        st.info("Run dbt to populate `MARTS.FACT_SALES`.")
    else:
        st.dataframe(
            filtered[["sales_date", "store_id", "dept_id", "weekly_sales", "baseline_forecast", "forecast_error"]],
            use_container_width=True,
            hide_index=True,
        )
