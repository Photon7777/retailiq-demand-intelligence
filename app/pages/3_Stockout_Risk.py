"""Stockout Risk page."""

from __future__ import annotations

import plotly.express as px
import streamlit as st

from src.app_support.streamlit_helpers import apply_global_styles, load_data, render_sidebar
from src.utils.snowflake_queries import fetch_stockout_risk_results

st.set_page_config(page_title="Stockout Risk", layout="wide")
apply_global_styles()
config = render_sidebar()

st.title("Stockout Risk")
st.write("Stockout risk from Phase 2 forecast outputs, with observed-demand proxy scoring before ML outputs are loaded.")

risk = load_data(fetch_stockout_risk_results, config)
risk_order = ["Critical", "High", "Medium", "Low"]
risk_counts = risk["risk_category"].value_counts().to_dict() if not risk.empty else {}

metric_cols = st.columns(4)
metric_cols[0].metric("Critical", f"{risk_counts.get('Critical', 0):,}")
metric_cols[1].metric("High", f"{risk_counts.get('High', 0):,}")
metric_cols[2].metric("Medium", f"{risk_counts.get('Medium', 0):,}")
metric_cols[3].metric("Low", f"{risk_counts.get('Low', 0):,}")

left, right = st.columns([1, 1])
with left:
    st.subheader("Risk Distribution")
    if risk.empty:
        st.info("No demand/inventory data available yet.")
    else:
        dist = risk["risk_category"].value_counts().reindex(risk_order, fill_value=0).reset_index()
        dist.columns = ["risk_category", "risk_count"]
        fig = px.bar(dist, x="risk_category", y="risk_count", color="risk_category")
        fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), showlegend=False, xaxis_title=None, yaxis_title="Rows")
        st.plotly_chart(fig, use_container_width=True)
with right:
    st.subheader("Recommended Actions")
    if risk.empty:
        st.info("Run dbt and the Phase 2 ML output load to populate stockout risk results.")
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
