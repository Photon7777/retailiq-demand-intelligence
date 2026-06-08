"""Stockout Risk page."""

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
    load_data,
    render_empty_state,
    render_metric_cards,
    render_page_header,
    render_section_header,
    render_sidebar,
)
from src.utils.snowflake_queries import fetch_stockout_risk_results

st.set_page_config(page_title="Stockout Risk", layout="wide")
apply_global_styles()
config = render_sidebar()

render_page_header(
    "Stockout Risk",
    "Inventory risk monitor",
    "Demand-to-inventory risk scoring with recommended replenishment actions by store, department, and date.",
    ["Critical queue", "Risk mix", "Recommended actions"],
)

risk = load_data(fetch_stockout_risk_results, config)
risk_order = ["Critical", "High", "Medium", "Low"]
risk_counts = risk["risk_category"].value_counts().to_dict() if not risk.empty else {}

render_metric_cards(
    [
        {"label": "Critical", "value": f"{risk_counts.get('Critical', 0):,}", "helper": "Demand exceeds inventory", "tone": "coral"},
        {"label": "High", "value": f"{risk_counts.get('High', 0):,}", "helper": "Immediate review", "tone": "amber"},
        {"label": "Medium", "value": f"{risk_counts.get('Medium', 0):,}", "helper": "Monitor closely", "tone": "blue"},
        {"label": "Low", "value": f"{risk_counts.get('Low', 0):,}", "helper": "Healthy coverage", "tone": "green"},
    ]
)

left, right = st.columns([1, 1])
with left:
    render_section_header("Risk Distribution", "Risk category count across scored demand rows.")
    if risk.empty:
        render_empty_state("No risk data", "Load demand and inventory marts to score stockout risk.")
    else:
        dist = risk["risk_category"].value_counts().reindex(risk_order, fill_value=0).reset_index()
        dist.columns = ["risk_category", "risk_count"]
        fig = px.bar(dist, x="risk_category", y="risk_count", color="risk_category")
        fig.update_layout(showlegend=False, xaxis_title=None, yaxis_title="Rows")
        configure_plotly_chart(fig, height=380)
        st.plotly_chart(fig, use_container_width=True)
with right:
    render_section_header("Recommended Actions", "Highest-priority replenishment queue.")
    if risk.empty:
        render_empty_state("No action queue", "Run dbt and load Phase 2 ML outputs to populate stockout risk results.")
    else:
        ordered_risk = risk.copy()
        ordered_risk["risk_sort"] = ordered_risk["risk_category"].map({name: index for index, name in enumerate(risk_order)})
        ordered_risk = ordered_risk.sort_values(["risk_sort", "stockout_risk_score"], ascending=[True, False])
        st.dataframe(
            ordered_risk[
                [
                    "risk_date",
                    "store_id",
                    "dept_id",
                    "predicted_demand",
                    "available_inventory",
                    "stockout_risk_score",
                    "risk_category",
                    "recommended_action",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )
