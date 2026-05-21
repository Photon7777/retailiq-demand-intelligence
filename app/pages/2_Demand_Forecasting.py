"""Demand Forecasting page."""

from __future__ import annotations

import plotly.express as px
import streamlit as st

from src.app_support.streamlit_helpers import apply_global_styles, format_currency, load_data, render_sidebar
from src.utils.snowflake_queries import fetch_forecast_results

st.set_page_config(page_title="Demand Forecasting", layout="wide")
apply_global_styles()
config = render_sidebar()

st.title("Demand Forecasting")
st.write("Forecast results from the Phase 2 ML output mart, with a simple baseline fallback before ML outputs are loaded.")

forecast = load_data(fetch_forecast_results, config)

filter_cols = st.columns(3)
store_options = ["All stores"] + sorted(forecast["store_id"].dropna().astype(int).unique().tolist()) if not forecast.empty else ["All stores"]
dept_options = (
    ["All departments"] + sorted(forecast["dept_id"].dropna().astype(int).unique().tolist()) if not forecast.empty else ["All departments"]
)
selected_store = filter_cols[0].selectbox("Store", store_options)
selected_dept = filter_cols[1].selectbox("Department", dept_options)
selected_horizon = filter_cols[2].selectbox(
    "Forecast Horizon",
    ["All horizons"] + sorted(forecast["horizon_days"].dropna().astype(int).unique().tolist()) if not forecast.empty else ["All horizons"],
)

filtered = forecast.copy()
if selected_store != "All stores" and not filtered.empty:
    filtered = filtered[filtered["store_id"] == selected_store]
if selected_dept != "All departments" and not filtered.empty:
    filtered = filtered[filtered["dept_id"] == selected_dept]
if selected_horizon != "All horizons" and not filtered.empty:
    filtered = filtered[filtered["horizon_days"] == selected_horizon]

if not filtered.empty:
    scored = filtered.dropna(subset=["actual_demand", "absolute_error"])
    wape = 0 if scored.empty or scored["actual_demand"].abs().sum() == 0 else scored["absolute_error"].sum() / scored["actual_demand"].abs().sum()
    metric_cols = st.columns(3)
    metric_cols[0].metric("Predicted Demand", format_currency(filtered["predicted_demand"].sum()))
    metric_cols[1].metric("WAPE", f"{wape:.1%}")
    metric_cols[2].metric("Records", f"{len(filtered):,}")

chart_col, table_col = st.columns([1.3, 1])
with chart_col:
    st.subheader("Actual vs Baseline")
    if filtered.empty:
        st.info("No forecast baseline data available yet.")
    else:
        chart_df = filtered.dropna(subset=["actual_demand"]).melt(
            id_vars=["forecast_date", "store_id", "dept_id"],
            value_vars=["actual_demand", "predicted_demand"],
            var_name="series",
            value_name="sales",
        )
        fig = px.line(chart_df, x="forecast_date", y="sales", color="series", markers=True)
        fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), yaxis_title="Sales", xaxis_title=None)
        st.plotly_chart(fig, use_container_width=True)
with table_col:
    st.subheader("Forecast Detail")
    if filtered.empty:
        st.info("Run dbt to populate `MARTS.FACT_SALES`.")
    else:
        st.dataframe(
            filtered[
                [
                    "forecast_date",
                    "store_id",
                    "dept_id",
                    "horizon_days",
                    "actual_demand",
                    "predicted_demand",
                    "prediction_interval_lower",
                    "prediction_interval_upper",
                    "forecast_error",
                    "model_version",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )
