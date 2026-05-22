"""Demand Forecasting page."""

from __future__ import annotations

from pathlib import Path
import sys

import plotly.express as px
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from src.app_support.streamlit_helpers import apply_global_styles, format_currency, format_number, load_data, render_sidebar
from src.utils.snowflake_queries import (
    fetch_forecast_detail,
    fetch_forecast_filter_options,
    fetch_forecast_metrics,
    fetch_forecast_trend,
)


def _all_label(value: int | None, label: str) -> str:
    return f"All {label}" if value is None else str(value)


def _compact_currency(value: float | int | None) -> str:
    """Keep large full-dataset totals readable in Streamlit metric cards."""
    if value is None:
        return "$0"
    amount = float(value)
    for suffix, divisor in (("B", 1_000_000_000), ("M", 1_000_000), ("K", 1_000)):
        if abs(amount) >= divisor:
            return f"${amount / divisor:,.2f}{suffix}"
    return format_currency(amount)


st.set_page_config(page_title="Demand Forecasting", layout="wide")
apply_global_styles()
config = render_sidebar()

st.title("Demand Forecasting")
st.write("Forecast performance from Snowflake-backed ML marts, aggregated for fast exploration on the full dataset.")

options = load_data(fetch_forecast_filter_options, config)
if options.empty:
    st.info("No forecast data available yet. Load ML outputs and run dbt to populate `MARTS.FACT_FORECAST`.")
    st.stop()

store_options: list[int | None] = [None] + sorted(options["store_id"].dropna().astype(int).unique().tolist())
dept_options: list[int | None] = [None] + sorted(options["dept_id"].dropna().astype(int).unique().tolist())
horizon_values = sorted(options["horizon_days"].dropna().astype(int).unique().tolist())
horizon_options: list[int | None] = [None] + horizon_values
horizon_default_index = horizon_options.index(0) if 0 in horizon_options else 0

filter_cols = st.columns([1, 1, 1, 1])
selected_store = filter_cols[0].selectbox(
    "Store",
    store_options,
    format_func=lambda value: _all_label(value, "stores"),
)
selected_dept = filter_cols[1].selectbox(
    "Department",
    dept_options,
    format_func=lambda value: _all_label(value, "departments"),
)
selected_horizon = filter_cols[2].selectbox(
    "Forecast Horizon",
    horizon_options,
    index=horizon_default_index,
    format_func=lambda value: "All horizons" if value is None else f"{value} days",
)
detail_limit = filter_cols[3].selectbox("Detail Rows", [100, 250, 500, 1000], index=1)

metrics = load_data(
    fetch_forecast_metrics,
    config,
    store_id=selected_store,
    dept_id=selected_dept,
    horizon_days=selected_horizon,
)
trend = load_data(
    fetch_forecast_trend,
    config,
    store_id=selected_store,
    dept_id=selected_dept,
    horizon_days=selected_horizon,
)
detail = load_data(
    fetch_forecast_detail,
    config,
    store_id=selected_store,
    dept_id=selected_dept,
    horizon_days=selected_horizon,
    limit=detail_limit,
)

if metrics.empty:
    st.info("No forecast rows match the current filters.")
    st.stop()

metric_row = metrics.iloc[0]
metric_cols = st.columns(4)
metric_cols[0].metric("Predicted Demand", _compact_currency(metric_row.get("predicted_demand")))
metric_cols[1].metric("Actual Demand", _compact_currency(metric_row.get("actual_demand")))
wape = metric_row.get("wape")
metric_cols[2].metric("WAPE", "N/A" if wape is None or wape != wape else f"{float(wape):.1%}")
metric_cols[3].metric("Forecast Rows", format_number(metric_row.get("forecast_rows")))

chart_col, table_col = st.columns([1.35, 1])
with chart_col:
    st.subheader("Weekly Actual vs Forecast")
    if trend.empty:
        st.info("No trend data matches the current filters.")
    else:
        chart_df = trend.melt(
            id_vars=["forecast_date"],
            value_vars=["actual_demand", "predicted_demand"],
            var_name="series",
            value_name="demand",
        ).dropna(subset=["demand"])
        fig = px.line(chart_df, x="forecast_date", y="demand", color="series", markers=False)
        fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), yaxis_title="Demand", xaxis_title=None)
        st.plotly_chart(fig, use_container_width=True)

with table_col:
    st.subheader("Forecast Detail")
    if detail.empty:
        st.info("No detail rows match the current filters.")
    else:
        st.dataframe(
            detail[
                [
                    "forecast_date",
                    "store_id",
                    "dept_id",
                    "horizon_days",
                    "actual_demand",
                    "predicted_demand",
                    "forecast_error",
                    "absolute_error",
                    "model_version",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

if not trend.empty and "wape" in trend.columns:
    st.subheader("Weekly Error")
    error_df = trend.dropna(subset=["wape"]).copy()
    if error_df.empty:
        st.info("WAPE is not available for unscored future horizon rows.")
    else:
        fig = px.bar(error_df, x="forecast_date", y="wape")
        fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), yaxis_title="WAPE", xaxis_title=None)
        st.plotly_chart(fig, use_container_width=True)
