"""Shared Streamlit helpers for RetailIQ pages."""

from __future__ import annotations

from dataclasses import replace
from html import escape
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
        :root {
            --retailiq-bg: #080d12;
            --retailiq-panel: #0f1720;
            --retailiq-panel-soft: #121d28;
            --retailiq-line: rgba(148, 163, 184, 0.22);
            --retailiq-text: #f8fafc;
            --retailiq-muted: #9aa7b5;
            --retailiq-teal: #2dd4bf;
            --retailiq-blue: #60a5fa;
            --retailiq-amber: #fbbf24;
            --retailiq-coral: #fb7185;
            --retailiq-green: #34d399;
        }

        .stApp {
            background:
                linear-gradient(180deg, rgba(12, 18, 25, 0.96), rgba(8, 13, 18, 1) 420px),
                var(--retailiq-bg);
            color: var(--retailiq-text);
        }

        .main .block-container {
            padding-top: 1.35rem;
            padding-bottom: 3rem;
            max-width: 1240px;
        }

        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #101923 0%, #0b1118 100%);
            border-right: 1px solid var(--retailiq-line);
        }

        section[data-testid="stSidebar"] h1 {
            letter-spacing: 0;
            font-weight: 780;
        }

        div[data-testid="stSidebarNav"] a {
            border-radius: 8px;
            margin: 0.15rem 0.25rem;
        }

        div[data-testid="stMetric"] {
            background: linear-gradient(180deg, rgba(18, 29, 40, 0.98), rgba(13, 21, 30, 0.98));
            border: 1px solid var(--retailiq-line);
            border-radius: 8px;
            padding: 0.8rem 1rem;
            box-shadow: 0 12px 28px rgba(0, 0, 0, 0.18);
        }

        div[data-testid="stMetric"] label {
            color: var(--retailiq-muted);
        }

        div[data-testid="stMetricValue"] {
            color: var(--retailiq-text);
            letter-spacing: 0;
        }

        div[data-testid="stDataFrame"],
        div[data-testid="stTable"] {
            border-radius: 8px;
            overflow: hidden;
        }

        div[data-testid="stAlert"] {
            border-radius: 8px;
            border: 1px solid rgba(96, 165, 250, 0.22);
        }

        .retailiq-hero {
            border: 1px solid var(--retailiq-line);
            border-radius: 8px;
            padding: 1.15rem 1.25rem;
            margin-bottom: 1rem;
            background:
                linear-gradient(135deg, rgba(45, 212, 191, 0.12), rgba(96, 165, 250, 0.08) 45%, rgba(251, 191, 36, 0.07)),
                linear-gradient(180deg, rgba(18, 29, 40, 0.98), rgba(11, 17, 24, 0.98));
            box-shadow: 0 18px 42px rgba(0, 0, 0, 0.22);
        }

        .retailiq-eyebrow {
            color: var(--retailiq-teal);
            font-size: 0.76rem;
            font-weight: 760;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 0.35rem;
        }

        .retailiq-hero h1 {
            font-size: clamp(2rem, 4vw, 3.05rem);
            line-height: 1.05;
            letter-spacing: 0;
            margin: 0;
            color: var(--retailiq-text);
        }

        .retailiq-hero p {
            color: #cbd5e1;
            max-width: 840px;
            margin: 0.7rem 0 0;
            font-size: 1rem;
            line-height: 1.55;
        }

        .retailiq-badges {
            display: flex;
            flex-wrap: wrap;
            gap: 0.45rem;
            margin-top: 0.9rem;
        }

        .retailiq-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            color: #dbeafe;
            background: rgba(96, 165, 250, 0.12);
            border: 1px solid rgba(96, 165, 250, 0.28);
            border-radius: 999px;
            padding: 0.28rem 0.62rem;
            font-size: 0.78rem;
            font-weight: 650;
            white-space: nowrap;
        }

        .retailiq-section {
            margin: 1.2rem 0 0.65rem;
        }

        .retailiq-section h2 {
            font-size: 1.12rem;
            letter-spacing: 0;
            margin: 0;
            color: var(--retailiq-text);
        }

        .retailiq-section p {
            margin: 0.25rem 0 0;
            color: var(--retailiq-muted);
            font-size: 0.9rem;
        }

        .retailiq-metric-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.75rem;
            margin: 0.65rem 0 1rem;
        }

        .retailiq-metric-card {
            min-height: 104px;
            border: 1px solid var(--retailiq-line);
            border-radius: 8px;
            padding: 0.85rem 0.9rem;
            background: linear-gradient(180deg, rgba(18, 29, 40, 0.98), rgba(12, 19, 27, 0.98));
            box-shadow: 0 14px 28px rgba(0, 0, 0, 0.18);
        }

        .retailiq-metric-card[data-tone="teal"] { border-top: 3px solid var(--retailiq-teal); }
        .retailiq-metric-card[data-tone="blue"] { border-top: 3px solid var(--retailiq-blue); }
        .retailiq-metric-card[data-tone="amber"] { border-top: 3px solid var(--retailiq-amber); }
        .retailiq-metric-card[data-tone="coral"] { border-top: 3px solid var(--retailiq-coral); }
        .retailiq-metric-card[data-tone="green"] { border-top: 3px solid var(--retailiq-green); }

        .retailiq-metric-label {
            color: var(--retailiq-muted);
            font-size: 0.76rem;
            font-weight: 720;
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }

        .retailiq-metric-value {
            color: var(--retailiq-text);
            font-size: clamp(1.35rem, 2vw, 2rem);
            line-height: 1.05;
            font-weight: 780;
            letter-spacing: 0;
            margin-top: 0.45rem;
            overflow-wrap: anywhere;
        }

        .retailiq-metric-helper {
            color: var(--retailiq-muted);
            font-size: 0.78rem;
            margin-top: 0.45rem;
        }

        .retailiq-status-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.65rem;
            margin: 0.6rem 0 1rem;
        }

        .retailiq-status-item {
            border: 1px solid var(--retailiq-line);
            border-radius: 8px;
            padding: 0.68rem 0.75rem;
            background: rgba(18, 29, 40, 0.72);
        }

        .retailiq-status-label {
            color: var(--retailiq-muted);
            font-size: 0.75rem;
        }

        .retailiq-status-value {
            color: var(--retailiq-text);
            font-size: 1.05rem;
            font-weight: 760;
            margin-top: 0.15rem;
        }

        .retailiq-empty {
            border: 1px dashed rgba(148, 163, 184, 0.36);
            border-radius: 8px;
            padding: 1rem;
            color: var(--retailiq-muted);
            background: rgba(18, 29, 40, 0.45);
        }

        .retailiq-empty strong {
            color: var(--retailiq-text);
            display: block;
            margin-bottom: 0.2rem;
        }

        .retailiq-answer {
            border: 1px solid rgba(45, 212, 191, 0.24);
            border-radius: 8px;
            padding: 1rem;
            background: linear-gradient(180deg, rgba(13, 28, 34, 0.94), rgba(12, 19, 27, 0.94));
            color: #d1fae5;
            min-height: 112px;
        }

        @media (max-width: 900px) {
            .retailiq-metric-grid,
            .retailiq-status-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
        }

        @media (max-width: 560px) {
            .main .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
            }
            .retailiq-metric-grid,
            .retailiq-status-grid {
                grid-template-columns: 1fr;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(title: str, eyebrow: str, description: str, badges: list[str] | None = None) -> None:
    """Render a consistent page header."""
    badge_html = ""
    if badges:
        badge_html = "<div class='retailiq-badges'>" + "".join(
            f"<span class='retailiq-badge'>{escape(badge)}</span>" for badge in badges
        ) + "</div>"
    st.markdown(
        f"""
        <div class="retailiq-hero">
            <div class="retailiq-eyebrow">{escape(eyebrow)}</div>
            <h1>{escape(title)}</h1>
            <p>{escape(description)}</p>
            {badge_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_header(title: str, caption: str | None = None) -> None:
    """Render a compact section heading."""
    caption_html = f"<p>{escape(caption)}</p>" if caption else ""
    st.markdown(
        f"""
        <div class="retailiq-section">
            <h2>{escape(title)}</h2>
            {caption_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_cards(metrics: list[dict[str, str | None]]) -> None:
    """Render dashboard metric cards."""
    cards = []
    for metric in metrics:
        tone = escape(metric.get("tone") or "teal")
        label = escape(metric.get("label") or "")
        value = escape(metric.get("value") or "0")
        helper = metric.get("helper")
        helper_html = f"<div class='retailiq-metric-helper'>{escape(helper)}</div>" if helper else ""
        cards.append(
            f"<div class='retailiq-metric-card' data-tone='{tone}'>"
            f"<div class='retailiq-metric-label'>{label}</div>"
            f"<div class='retailiq-metric-value'>{value}</div>"
            f"{helper_html}"
            "</div>"
        )
    st.markdown(f"<div class='retailiq-metric-grid'>{''.join(cards)}</div>", unsafe_allow_html=True)


def render_status_grid(items: list[tuple[str, str]]) -> None:
    """Render small operational status items."""
    cells = []
    for label, value in items:
        cells.append(
            "<div class='retailiq-status-item'>"
            f"<div class='retailiq-status-label'>{escape(label)}</div>"
            f"<div class='retailiq-status-value'>{escape(value)}</div>"
            "</div>"
        )
    st.markdown(f"<div class='retailiq-status-grid'>{''.join(cells)}</div>", unsafe_allow_html=True)


def render_empty_state(title: str, body: str) -> None:
    """Render a consistent empty state."""
    st.markdown(
        f"<div class='retailiq-empty'><strong>{escape(title)}</strong>{escape(body)}</div>",
        unsafe_allow_html=True,
    )


def render_answer_panel(answer: str) -> None:
    """Render an analyst answer panel."""
    st.markdown(f"<div class='retailiq-answer'>{escape(answer)}</div>", unsafe_allow_html=True)


def configure_plotly_chart(fig, height: int = 360):
    """Apply the RetailIQ chart theme."""
    fig.update_layout(
        template="plotly_dark",
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(8,13,18,0.42)",
        font=dict(color="#dbe4ee", size=12),
        colorway=["#2dd4bf", "#60a5fa", "#fbbf24", "#fb7185", "#34d399", "#a78bfa"],
        margin=dict(l=8, r=8, t=16, b=8),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(gridcolor="rgba(148, 163, 184, 0.14)", zerolinecolor="rgba(148, 163, 184, 0.22)")
    fig.update_yaxes(gridcolor="rgba(148, 163, 184, 0.14)", zerolinecolor="rgba(148, 163, 184, 0.22)")
    return fig


def active_config() -> AppConfig:
    """Return config with the current Streamlit MFA passcode, when provided."""
    config = get_config()
    if is_key_pair_auth(config):
        return config
    passcode = st.session_state.get("snowflake_mfa_code", "").strip()
    if passcode:
        return replace(config, snowflake_passcode=passcode)
    return config


def is_key_pair_auth(config: AppConfig) -> bool:
    """Return whether Snowflake is configured for service-account key-pair auth."""
    return (config.snowflake_authenticator or "").lower() == "snowflake_jwt"


def render_sidebar() -> AppConfig:
    """Render a consistent sidebar and return the active Snowflake config."""
    with st.sidebar:
        st.title("RetailIQ")
        st.caption("Demand intelligence platform")
        st.divider()
        st.markdown("**Snowflake**")
        config = get_config()
        if is_key_pair_auth(config):
            st.caption("Using deployed key-pair authentication.")
        else:
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


def load_data(_loader: Callable[..., pd.DataFrame], config: AppConfig, *args, **kwargs) -> pd.DataFrame:
    """Run a Snowflake-backed loader and display a graceful message on failure."""
    try:
        return _loader(*args, config=config, **kwargs)
    except Exception as exc:  # noqa: BLE001 - Streamlit should stay up during setup/auth issues
        st.warning(f"Unable to load Snowflake data: {exc}")
        return pd.DataFrame()


def format_currency(value: float | int | None) -> str:
    """Format currency for metric cards."""
    if value is None or pd.isna(value):
        return "$0"
    return f"${float(value):,.0f}"


def format_compact_currency(value: float | int | None) -> str:
    """Format large currency values for compact dashboard cards."""
    if value is None or pd.isna(value):
        return "$0"
    amount = float(value)
    for suffix, divisor in (("B", 1_000_000_000), ("M", 1_000_000), ("K", 1_000)):
        if abs(amount) >= divisor:
            return f"${amount / divisor:,.2f}{suffix}"
    return format_currency(amount)


def format_number(value: float | int | None) -> str:
    """Format numeric metrics."""
    if value is None or pd.isna(value):
        return "0"
    return f"{float(value):,.0f}"
