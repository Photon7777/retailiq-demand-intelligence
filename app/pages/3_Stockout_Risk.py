"""Stockout Risk page."""

from __future__ import annotations

import streamlit as st


st.set_page_config(page_title="Stockout Risk", layout="wide")

st.title("Stockout Risk")
st.write("Prioritize store-department combinations where predicted demand may exceed available inventory.")

metric_cols = st.columns(4)
metric_cols[0].metric("Critical", "TBD")
metric_cols[1].metric("High", "TBD")
metric_cols[2].metric("Medium", "TBD")
metric_cols[3].metric("Low", "TBD")

left, right = st.columns([1, 1])
with left:
    st.subheader("Risk Distribution")
    st.bar_chart({"risk_count": []})
with right:
    st.subheader("Recommended Actions")
    st.dataframe(
        {"store": [], "department": [], "risk_category": [], "recommended_action": []},
        use_container_width=True,
        hide_index=True,
    )

# TODO: Connect to stockout risk outputs generated from forecast and inventory data.
