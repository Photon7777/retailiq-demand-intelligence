"""Pipeline Health page."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import plotly.express as px
import streamlit as st


ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from src.app_support.streamlit_helpers import (  # noqa: E402
    apply_global_styles,
    configure_plotly_chart,
    format_number,
    load_data,
    render_action_cards,
    render_empty_state,
    render_metric_cards,
    render_page_header,
    render_pipeline_rail,
    render_section_header,
    render_sidebar,
    render_status_grid,
)
from src.utils.snowflake_queries import fetch_pipeline_health, fetch_quality_checks  # noqa: E402


def _format_timestamp(value: object) -> str:
    timestamp = pd.to_datetime(value, errors="coerce")
    if pd.isna(timestamp):
        return "Not available"
    return timestamp.strftime("%b %d, %Y %I:%M %p")


def _stage_status(summary: pd.DataFrame, stage: str) -> str:
    rows = summary[summary["pipeline_stage"] == stage]
    if rows.empty:
        return "Not found"
    row = rows.iloc[0]
    if int(row["review_objects"]) == 0:
        return "Ready"
    return f"{int(row['review_objects'])} to review"


st.set_page_config(page_title="Pipeline Health", layout="wide")
apply_global_styles()
config = render_sidebar()

render_page_header(
    "Pipeline Health",
    "Orchestration command center",
    "A Snowflake-backed control view for raw ingestion, dbt models, ML outputs, and freshness signals.",
    ["Airflow DAG", "Snowflake metadata", "dbt readiness", "ML outputs"],
)

health = load_data(fetch_pipeline_health, config)
quality = load_data(fetch_quality_checks, config)

if health.empty:
    render_empty_state("No pipeline metadata", "Run the Snowflake setup, data load, ML output load, and dbt build to populate pipeline health.")
    st.stop()

health = health.copy()
health["row_count"] = pd.to_numeric(health["row_count"], errors="coerce").fillna(0)
health["last_altered"] = pd.to_datetime(health["last_altered"], errors="coerce")
health["created"] = pd.to_datetime(health["created"], errors="coerce")

stage_order = {
    "Raw ingestion": 1,
    "dbt staging": 2,
    "dbt marts": 3,
    "ML outputs": 4,
    "Model marts": 5,
}
stage_summary = (
    health.groupby("pipeline_stage", as_index=False)
    .agg(
        total_objects=("object_name", "count"),
        ready_objects=("status", lambda values: int((values == "Ready").sum())),
        review_objects=("status", lambda values: int((values != "Ready").sum())),
        row_count=("row_count", "sum"),
        last_altered=("last_altered", "max"),
    )
)
stage_summary["stage_order"] = stage_summary["pipeline_stage"].map(stage_order).fillna(99)
stage_summary = stage_summary.sort_values("stage_order").drop(columns=["stage_order"])

latest_refresh = health["last_altered"].dropna().max()
ready_objects = int((health["status"] == "Ready").sum())
review_objects = int((health["status"] != "Ready").sum())
base_tables = int((health["object_type"] == "BASE TABLE").sum())
warehouse_rows = int(health["row_count"].sum())

render_metric_cards(
    [
        {"label": "Latest Refresh", "value": _format_timestamp(latest_refresh), "helper": "Max Snowflake last altered", "tone": "lime"},
        {"label": "Objects Ready", "value": f"{ready_objects}/{len(health)}", "helper": "Expected pipeline objects", "tone": "blue"},
        {"label": "Rows Tracked", "value": format_number(warehouse_rows), "helper": "Raw, mart, and ML rows", "tone": "green"},
        {"label": "Review Items", "value": format_number(review_objects), "helper": "Missing or empty objects", "tone": "amber" if review_objects else "mint"},
    ]
)

render_status_grid(
    [
        ("Raw ingestion", _stage_status(stage_summary, "Raw ingestion")),
        ("dbt staging", _stage_status(stage_summary, "dbt staging")),
        ("dbt marts", _stage_status(stage_summary, "dbt marts")),
        ("ML outputs", _stage_status(stage_summary, "ML outputs")),
        ("Model marts", _stage_status(stage_summary, "Model marts")),
    ]
)

render_section_header("Refresh Path", "The local Airflow DAG updates these Snowflake-backed product layers.")
render_pipeline_rail(
    [
        ("Source validation", "Confirm Walmart sales, store, and feature files"),
        ("Data preparation", "Create canonical sales, inventory, and weather files"),
        ("Raw Snowflake load", "Refresh RAW tables with repeatable truncation"),
        ("Model scoring", "Train forecast model and generate ML outputs"),
        ("dbt build", "Promote raw and ML tables into governed marts"),
        ("Streamlit serve", "Read compact mart and metadata queries"),
    ]
)

summary_col, chart_col = st.columns([1, 1])
with summary_col:
    render_section_header("Layer Summary", "Expected object coverage by pipeline stage.")
    st.dataframe(
        stage_summary.assign(
            row_count=lambda df: df["row_count"].astype(int),
            last_altered=lambda df: df["last_altered"].map(_format_timestamp),
        ),
        use_container_width=True,
        hide_index=True,
    )

with chart_col:
    render_section_header("Rows By Layer", "Snowflake row counts for tracked base tables.")
    row_chart = stage_summary[stage_summary["row_count"] > 0].copy()
    if row_chart.empty:
        render_empty_state("No row counts", "Base-table row counts will appear after data is loaded.")
    else:
        fig = px.bar(
            row_chart,
            x="pipeline_stage",
            y="row_count",
            color="pipeline_stage",
            text="row_count",
        )
        fig.update_layout(xaxis_title=None, yaxis_title="Rows", showlegend=False)
        fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside", cliponaxis=False)
        configure_plotly_chart(fig, height=330)
        st.plotly_chart(fig, use_container_width=True)

tab_objects, tab_quality, tab_runbook = st.tabs(["Object Health", "Quality Signals", "Runbook"])

with tab_objects:
    render_section_header("Expected Objects", "Object status from Snowflake information schema.")
    object_view = health[
        [
            "pipeline_stage",
            "object_name",
            "description",
            "object_type",
            "row_count",
            "status",
            "last_altered",
        ]
    ].copy()
    object_view["row_count"] = object_view["row_count"].astype(int)
    object_view["last_altered"] = object_view["last_altered"].map(_format_timestamp)
    st.dataframe(object_view, use_container_width=True, hide_index=True)

with tab_quality:
    render_section_header("Data Quality Signals", "Current warehouse object checks used by the Data Quality page.")
    if quality.empty:
        render_empty_state("No quality checks", "Quality checks will appear after Snowflake metadata is available.")
    else:
        quality_view = quality.copy()
        if "last_altered" in quality_view.columns:
            quality_view["last_altered"] = quality_view["last_altered"].map(_format_timestamp)
        st.dataframe(quality_view, use_container_width=True, hide_index=True)

with tab_runbook:
    render_section_header("Operational Notes", "How to refresh and validate the pipeline locally.")
    render_action_cards(
        [
            ("Airflow trigger", "Open localhost:8081, trigger retailiq_phase2_pipeline, and watch the grid until dbt_test_marts succeeds."),
            ("Snowflake check", "Confirm RAW, ML, and MARTS objects have fresh last_altered timestamps and non-zero row counts."),
            ("Public app refresh", "After a successful run, use Refresh data in the sidebar so Streamlit clears cached Snowflake results."),
        ]
    )
    st.caption(f"Tracked base tables: {base_tables}. Health source: Snowflake information schema.")
