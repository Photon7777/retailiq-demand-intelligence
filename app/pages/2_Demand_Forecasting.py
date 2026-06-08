"""Demand Forecasting page."""

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
from src.utils.snowflake_queries import (
    fetch_forecast_detail,
    fetch_forecast_filter_options,
    fetch_forecast_metrics,
    fetch_forecast_trend,
)


def _all_label(value: int | None, label: str) -> str:
    return f"All {label}" if value is None else str(value)


st.set_page_config(page_title="Demand Forecasting", layout="wide")
apply_global_styles()
config = render_sidebar()

render_page_header(
    "Demand Forecasting",
    "Forecast control room",
    "Model output, error tracking, and store-department demand trends aggregated directly in Snowflake.",
    ["Actual vs forecast", "WAPE", "Store filters"],
)

options = load_data(fetch_forecast_filter_options, config)
if options.empty:
    render_empty_state("No forecast data", "Load ML outputs and run dbt to populate MARTS.FACT_FORECAST.")
    st.stop()

store_options: list[int | None] = [None] + sorted(options["store_id"].dropna().astype(int).unique().tolist())
dept_options: list[int | None] = [None] + sorted(options["dept_id"].dropna().astype(int).unique().tolist())
horizon_values = sorted(options["horizon_days"].dropna().astype(int).unique().tolist())
horizon_options: list[int | None] = [None] + horizon_values
horizon_default_index = horizon_options.index(0) if 0 in horizon_options else 0

render_section_header("Forecast Filters", "Scope the model results without pulling the full table into the app.")
with st.container(border=True):
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
    render_empty_state("No matching rows", "Adjust filters to broaden the forecast scope.")
    st.stop()

metric_row = metrics.iloc[0]
wape = metric_row.get("wape")
render_metric_cards(
    [
        {"label": "Predicted Demand", "value": format_compact_currency(metric_row.get("predicted_demand")), "helper": "Model estimate", "tone": "teal"},
        {"label": "Actual Demand", "value": format_compact_currency(metric_row.get("actual_demand")), "helper": "Observed sales demand", "tone": "blue"},
        {"label": "WAPE", "value": "N/A" if wape is None or wape != wape else f"{float(wape):.1%}", "helper": "Weighted error", "tone": "amber"},
        {"label": "Forecast Rows", "value": format_number(metric_row.get("forecast_rows")), "helper": "Rows in current scope", "tone": "green"},
    ]
)

chart_col, table_col = st.columns([1.35, 1])
with chart_col:
    render_section_header("Weekly Actual vs Forecast", "Trend comparison for the selected scope.")
    if trend.empty:
        render_empty_state("No trend data", "No forecast dates match the selected filters.")
    else:
        chart_df = trend.melt(
            id_vars=["forecast_date"],
            value_vars=["actual_demand", "predicted_demand"],
            var_name="series",
            value_name="demand",
        ).dropna(subset=["demand"])
        fig = px.line(chart_df, x="forecast_date", y="demand", color="series", markers=False)
        fig.update_layout(yaxis_title="Demand", xaxis_title=None)
        configure_plotly_chart(fig, height=430)
        st.plotly_chart(fig, use_container_width=True)

with table_col:
    render_section_header("Forecast Detail", "Recent forecast rows from Snowflake.")
    if detail.empty:
        render_empty_state("No detail rows", "No forecast rows match the current filters.")
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
    render_section_header("Weekly Error", "Weighted absolute percentage error by forecast date.")
    error_df = trend.dropna(subset=["wape"]).copy()
    if error_df.empty:
        render_empty_state("No WAPE", "WAPE is not available for unscored future horizon rows.")
    else:
        fig = px.bar(error_df, x="forecast_date", y="wape")
        fig.update_layout(yaxis_title="WAPE", xaxis_title=None)
        configure_plotly_chart(fig, height=320)
        st.plotly_chart(fig, use_container_width=True)
