"""Shared Streamlit helpers for RetailIQ pages."""

from __future__ import annotations

from dataclasses import replace
from typing import Callable, TypeVar

import pandas as pd
import streamlit as st

from src.utils.config import AppConfig, get_config
from src.utils.snowflake_connection import test_snowflake_connection


T = TypeVar("T")


def apply_global_styles() -> None:
    """Apply small shared layout refinements."""
    st.markdown(
        """
        <style>
        .main .block-container {
            padding-top: 2rem;
            max-width: 1180px;
        }
        div[data-testid="stMetric"] {
            border: 1px solid rgba(148, 163, 184, 0.25);
            border-radius: 8px;
            padding: 0.75rem 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def active_config() -> AppConfig:
    """Return config with the current Streamlit MFA passcode, when provided."""
    config = get_config()
    passcode = st.session_state.get("snowflake_mfa_code", "").strip()
    if passcode:
        return replace(config, snowflake_passcode=passcode)
    return config


def render_sidebar() -> AppConfig:
    """Render a consistent sidebar and return the active Snowflake config."""
    with st.sidebar:
        st.title("RetailIQ")
        st.caption("Demand intelligence platform")
        st.divider()
        st.markdown("**Snowflake**")
        st.text_input(
            "MFA code",
            key="snowflake_mfa_code",
            max_chars=6,
            type="password",
            help="Enter the current 6-digit Snowflake authenticator code before checking the connection.",
        )
        if st.button("Check connection", use_container_width=True):
            ok, message = test_snowflake_connection(active_config())
            st.session_state["snowflake_status"] = {"ok": ok, "message": message}
        status = st.session_state.get("snowflake_status")
        if status:
            if status["ok"]:
                st.success(status["message"])
            else:
                st.warning(status["message"])
        else:
            st.caption("Connection not checked in this session.")
        st.divider()
        if st.button("Refresh data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    return active_config()


def load_data(loader: Callable[..., pd.DataFrame], config: AppConfig, *args, **kwargs) -> pd.DataFrame:
    """Run a Snowflake-backed loader and display a graceful message on failure."""
    try:
        return loader(*args, config=config, **kwargs)
    except Exception as exc:  # noqa: BLE001 - Streamlit should stay up during setup/auth issues
        st.warning(f"Unable to load Snowflake data: {exc}")
        return pd.DataFrame()


def format_currency(value: float | int | None) -> str:
    """Format currency for metric cards."""
    if value is None or pd.isna(value):
        return "$0"
    return f"${float(value):,.0f}"


def format_number(value: float | int | None) -> str:
    """Format numeric metrics."""
    if value is None or pd.isna(value):
        return "0"
    return f"{float(value):,.0f}"

