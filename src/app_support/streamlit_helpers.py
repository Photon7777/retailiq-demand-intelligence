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
            --retailiq-bg: #050607;
            --retailiq-bg-2: #0a0d0b;
            --retailiq-panel: #111411;
            --retailiq-panel-soft: #161a15;
            --retailiq-panel-warm: #1b1711;
            --retailiq-line: rgba(238, 241, 226, 0.14);
            --retailiq-line-strong: rgba(238, 241, 226, 0.24);
            --retailiq-text: #f7f4ea;
            --retailiq-muted: #a6aa9c;
            --retailiq-lime: #b7f34b;
            --retailiq-cobalt: #48b8ff;
            --retailiq-citrus: #ffb84d;
            --retailiq-rose: #ff5f7e;
            --retailiq-mint: #43e6a8;
            --retailiq-violet: #a78bfa;
        }

        .stApp {
            background:
                linear-gradient(180deg, rgba(10, 13, 11, 0.96), rgba(5, 6, 7, 1) 480px),
                linear-gradient(135deg, rgba(183, 243, 75, 0.06), transparent 34%),
                repeating-linear-gradient(90deg, rgba(238, 241, 226, 0.035) 0, rgba(238, 241, 226, 0.035) 1px, transparent 1px, transparent 64px),
                var(--retailiq-bg);
            color: var(--retailiq-text);
        }

        .main .block-container {
            padding-top: 1.1rem;
            padding-bottom: 3rem;
            max-width: 1280px;
        }

        section[data-testid="stSidebar"] {
            background:
                linear-gradient(180deg, rgba(22, 26, 21, 0.98), rgba(7, 8, 8, 0.98)),
                repeating-linear-gradient(0deg, rgba(183, 243, 75, 0.04) 0, rgba(183, 243, 75, 0.04) 1px, transparent 1px, transparent 36px);
            border-right: 1px solid var(--retailiq-line);
        }

        section[data-testid="stSidebar"] h1 {
            letter-spacing: 0;
            font-weight: 780;
            color: var(--retailiq-text);
        }

        div[data-testid="stSidebarNav"] a {
            border-radius: 8px;
            margin: 0.15rem 0.25rem;
            color: #d8dacd;
        }

        div[data-testid="stSidebarNav"] a:hover {
            background: rgba(183, 243, 75, 0.09);
            color: var(--retailiq-text);
        }

        div[data-testid="stSidebarNav"] a[aria-current="page"] {
            background: linear-gradient(90deg, rgba(183, 243, 75, 0.18), rgba(72, 184, 255, 0.1));
            border: 1px solid rgba(183, 243, 75, 0.22);
        }

        .stButton > button,
        div[data-testid="stBaseButton-primary"] button,
        button[kind="primary"] {
            border-radius: 8px;
            border: 1px solid rgba(183, 243, 75, 0.34);
            background: linear-gradient(135deg, rgba(183, 243, 75, 0.18), rgba(72, 184, 255, 0.11));
            color: var(--retailiq-text);
            box-shadow: 0 10px 24px rgba(0, 0, 0, 0.22);
            font-weight: 720;
        }

        .stButton > button:hover,
        button[kind="primary"]:hover {
            border-color: rgba(183, 243, 75, 0.72);
            color: #ffffff;
            transform: translateY(-1px);
        }

        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-color: var(--retailiq-line-strong);
            border-radius: 8px;
            background: linear-gradient(180deg, rgba(17, 20, 17, 0.82), rgba(11, 13, 11, 0.74));
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.035);
        }

        div[data-baseweb="select"] > div,
        div[data-testid="stTextInput"] input {
            border-radius: 8px;
            border-color: rgba(238, 241, 226, 0.18);
            background: rgba(5, 6, 7, 0.72);
        }

        div[data-testid="stMetric"] {
            background: linear-gradient(180deg, rgba(22, 26, 21, 0.98), rgba(10, 12, 10, 0.98));
            border: 1px solid var(--retailiq-line);
            border-radius: 8px;
            padding: 0.8rem 1rem;
            box-shadow: 0 18px 34px rgba(0, 0, 0, 0.2);
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
            border: 1px solid var(--retailiq-line);
        }

        div[data-testid="stAlert"] {
            border-radius: 8px;
            border: 1px solid rgba(183, 243, 75, 0.18);
            background: rgba(49, 53, 24, 0.6);
        }

        div[data-testid="stSpinner"] {
            border: 1px solid rgba(183, 243, 75, 0.2);
            border-radius: 8px;
            padding: 0.72rem 0.85rem;
            background:
                linear-gradient(90deg, rgba(183, 243, 75, 0.12), rgba(72, 184, 255, 0.07)),
                rgba(14, 17, 14, 0.86);
            color: var(--retailiq-text);
            box-shadow: 0 14px 28px rgba(0, 0, 0, 0.22);
        }

        div[data-testid="stSpinner"] div {
            color: var(--retailiq-text);
            font-weight: 650;
        }

        .retailiq-hero {
            position: relative;
            overflow: hidden;
            border: 1px solid var(--retailiq-line-strong);
            border-radius: 8px;
            padding: 1.35rem 1.45rem 1.2rem;
            margin-bottom: 1.05rem;
            background:
                linear-gradient(90deg, rgba(183, 243, 75, 0.18), transparent 18%),
                linear-gradient(135deg, rgba(72, 184, 255, 0.13), rgba(255, 184, 77, 0.08) 48%, rgba(255, 95, 126, 0.09)),
                linear-gradient(180deg, rgba(22, 26, 21, 0.98), rgba(8, 9, 8, 0.98));
            box-shadow: 0 22px 54px rgba(0, 0, 0, 0.34);
        }

        .retailiq-hero::before {
            content: "";
            position: absolute;
            inset: 0;
            pointer-events: none;
            background:
                repeating-linear-gradient(90deg, transparent 0, transparent 30px, rgba(247, 244, 234, 0.035) 31px, transparent 32px),
                linear-gradient(180deg, rgba(255, 255, 255, 0.045), transparent 38%);
        }

        .retailiq-hero > * {
            position: relative;
            z-index: 1;
        }

        .retailiq-eyebrow {
            color: var(--retailiq-lime);
            font-size: 0.76rem;
            font-weight: 760;
            letter-spacing: 0.12em;
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
            color: #d5d9ca;
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
            color: #f7f4ea;
            background: rgba(5, 6, 7, 0.42);
            border: 1px solid rgba(238, 241, 226, 0.2);
            border-radius: 999px;
            padding: 0.28rem 0.62rem;
            font-size: 0.78rem;
            font-weight: 650;
            white-space: nowrap;
        }

        .retailiq-hero-rail {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.45rem;
            margin-top: 1rem;
        }

        .retailiq-hero-rail span {
            display: block;
            border-left: 3px solid var(--retailiq-lime);
            background: rgba(5, 6, 7, 0.34);
            border-radius: 8px;
            padding: 0.45rem 0.58rem;
            color: #dde3d1;
            font-size: 0.75rem;
            font-weight: 720;
            text-transform: uppercase;
            letter-spacing: 0.07em;
        }

        .retailiq-hero-rail span:nth-child(2) { border-left-color: var(--retailiq-cobalt); }
        .retailiq-hero-rail span:nth-child(3) { border-left-color: var(--retailiq-citrus); }
        .retailiq-hero-rail span:nth-child(4) { border-left-color: var(--retailiq-rose); }

        .retailiq-section {
            border-left: 3px solid rgba(183, 243, 75, 0.72);
            padding-left: 0.72rem;
            margin: 1.25rem 0 0.7rem;
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
            background:
                linear-gradient(135deg, rgba(255, 255, 255, 0.045), transparent 36%),
                linear-gradient(180deg, rgba(22, 26, 21, 0.98), rgba(9, 11, 9, 0.98));
            box-shadow: 0 16px 32px rgba(0, 0, 0, 0.24);
        }

        .retailiq-metric-card[data-tone="teal"],
        .retailiq-metric-card[data-tone="lime"] { border-top: 3px solid var(--retailiq-lime); }
        .retailiq-metric-card[data-tone="blue"],
        .retailiq-metric-card[data-tone="cobalt"] { border-top: 3px solid var(--retailiq-cobalt); }
        .retailiq-metric-card[data-tone="amber"],
        .retailiq-metric-card[data-tone="citrus"] { border-top: 3px solid var(--retailiq-citrus); }
        .retailiq-metric-card[data-tone="coral"],
        .retailiq-metric-card[data-tone="rose"] { border-top: 3px solid var(--retailiq-rose); }
        .retailiq-metric-card[data-tone="green"],
        .retailiq-metric-card[data-tone="mint"] { border-top: 3px solid var(--retailiq-mint); }
        .retailiq-metric-card[data-tone="violet"] { border-top: 3px solid var(--retailiq-violet); }

        .retailiq-metric-label {
            color: var(--retailiq-muted);
            font-size: 0.76rem;
            font-weight: 720;
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }

        .retailiq-metric-value {
            color: var(--retailiq-text);
            font-size: clamp(1.42rem, 2vw, 2.08rem);
            line-height: 1.05;
            font-weight: 820;
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
            background: rgba(22, 26, 21, 0.78);
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.035);
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
            background: rgba(22, 26, 21, 0.48);
        }

        .retailiq-empty strong {
            color: var(--retailiq-text);
            display: block;
            margin-bottom: 0.2rem;
        }

        .retailiq-answer {
            border: 1px solid rgba(183, 243, 75, 0.26);
            border-radius: 8px;
            padding: 1rem;
            background: linear-gradient(180deg, rgba(29, 35, 19, 0.94), rgba(12, 15, 11, 0.94));
            color: #ecffd0;
            min-height: 112px;
        }

        .retailiq-pipeline {
            display: grid;
            grid-template-columns: repeat(6, minmax(0, 1fr));
            gap: 0.55rem;
            margin: 0.75rem 0 1rem;
        }

        .retailiq-pipeline-step {
            min-height: 82px;
            border: 1px solid var(--retailiq-line);
            border-radius: 8px;
            padding: 0.72rem;
            background:
                linear-gradient(180deg, rgba(22, 26, 21, 0.88), rgba(8, 9, 8, 0.88));
            position: relative;
            overflow: hidden;
        }

        .retailiq-pipeline-step::after {
            content: "";
            position: absolute;
            left: 0;
            right: 0;
            bottom: 0;
            height: 3px;
            background: linear-gradient(90deg, var(--retailiq-lime), var(--retailiq-cobalt), var(--retailiq-citrus));
        }

        .retailiq-pipeline-index {
            color: var(--retailiq-lime);
            font-size: 0.72rem;
            font-weight: 820;
            margin-bottom: 0.28rem;
        }

        .retailiq-pipeline-title {
            color: var(--retailiq-text);
            font-size: 0.9rem;
            font-weight: 780;
        }

        .retailiq-pipeline-caption {
            color: var(--retailiq-muted);
            font-size: 0.74rem;
            margin-top: 0.22rem;
            line-height: 1.35;
        }

        .retailiq-card-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.75rem;
            margin: 0.65rem 0 1rem;
        }

        .retailiq-action-card {
            border: 1px solid var(--retailiq-line);
            border-radius: 8px;
            padding: 0.95rem;
            background:
                linear-gradient(135deg, rgba(72, 184, 255, 0.08), transparent 42%),
                rgba(22, 26, 21, 0.76);
            min-height: 132px;
        }

        .retailiq-action-card strong {
            color: var(--retailiq-text);
            font-size: 1rem;
        }

        .retailiq-action-card p {
            color: var(--retailiq-muted);
            line-height: 1.45;
            font-size: 0.88rem;
            margin: 0.38rem 0 0;
        }

        @media (max-width: 900px) {
            .retailiq-metric-grid,
            .retailiq-status-grid,
            .retailiq-pipeline,
            .retailiq-card-grid,
            .retailiq-hero-rail {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
        }

        @media (max-width: 560px) {
            .main .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
            }
            .retailiq-metric-grid,
            .retailiq-status-grid,
            .retailiq-pipeline,
            .retailiq-card-grid,
            .retailiq-hero-rail {
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
    hero_rail = (
        "<div class='retailiq-hero-rail'>"
        "<span>Demand sensing</span>"
        "<span>Inventory signal</span>"
        "<span>Forecast mart</span>"
        "<span>Analyst layer</span>"
        "</div>"
    )
    st.markdown(
        f"""
        <div class="retailiq-hero">
            <div class="retailiq-eyebrow">{escape(eyebrow)}</div>
            <h1>{escape(title)}</h1>
            <p>{escape(description)}</p>
            {badge_html}
            {hero_rail}
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


def render_pipeline_rail(steps: list[tuple[str, str]]) -> None:
    """Render a compact architecture rail."""
    cells = []
    for index, (title, caption) in enumerate(steps, start=1):
        cells.append(
            "<div class='retailiq-pipeline-step'>"
            f"<div class='retailiq-pipeline-index'>{index:02d}</div>"
            f"<div class='retailiq-pipeline-title'>{escape(title)}</div>"
            f"<div class='retailiq-pipeline-caption'>{escape(caption)}</div>"
            "</div>"
        )
    st.markdown(f"<div class='retailiq-pipeline'>{''.join(cells)}</div>", unsafe_allow_html=True)


def render_action_cards(cards: list[tuple[str, str]]) -> None:
    """Render feature cards for roadmap and workflow sections."""
    card_html = []
    for title, body in cards:
        card_html.append(
            "<div class='retailiq-action-card'>"
            f"<strong>{escape(title)}</strong>"
            f"<p>{escape(body)}</p>"
            "</div>"
        )
    st.markdown(f"<div class='retailiq-card-grid'>{''.join(card_html)}</div>", unsafe_allow_html=True)


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
        plot_bgcolor="rgba(5,6,7,0.36)",
        font=dict(color="#edeedf", size=12),
        colorway=["#b7f34b", "#48b8ff", "#ffb84d", "#ff5f7e", "#43e6a8", "#a78bfa"],
        margin=dict(l=8, r=8, t=16, b=8),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(gridcolor="rgba(238, 241, 226, 0.11)", zerolinecolor="rgba(238, 241, 226, 0.18)")
    fig.update_yaxes(gridcolor="rgba(238, 241, 226, 0.11)", zerolinecolor="rgba(238, 241, 226, 0.18)")
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
            with st.spinner("Checking Snowflake connection..."):
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


def load_data(
    _loader: Callable[..., pd.DataFrame],
    config: AppConfig,
    *args,
    loading_message: str | None = None,
    **kwargs,
) -> pd.DataFrame:
    """Run a Snowflake-backed loader and display a graceful message on failure."""
    loader_name = getattr(_loader, "__name__", "Snowflake data").replace("fetch_", "").replace("_", " ")
    message = loading_message or f"Loading {loader_name}..."
    try:
        with st.spinner(message):
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
