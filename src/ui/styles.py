"""Enterprise theme application for the Streamlit UI.

Two concerns:
1. ``apply_enterprise_theme()`` — injects the global stylesheet (IBM Plex,
   dark tokens, focus rings, button overrides, reduced-motion, status banner
   accents).  Called once from ``render_app``.
2. ``panel_header()`` / ``caption()`` / ``section_header()`` — thin helpers
   that emit semantic markup matching DESIGN.md so panels and titles stay
   consistent across tabs without every caller hand-rolling markdown.
"""
from __future__ import annotations

from textwrap import dedent

import streamlit as st


TOKENS = {
    "primary": "#0C5CAB",
    "secondary": "#0a4a8a",
    "success": "#10b981",
    "warning": "#f59e0b",
    "danger": "#ef4444",
    "surface": "#09090b",
    "surface-panel": "#141417",
    "border-subtle": "#27272a",
    "text": "#fafafa",
    "text-muted": "#a1a1aa",
    "text-soft": "#71717a",
}


_THEME_CSS = dedent(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap');

    :root {
        --primary: #0C5CAB;
        --secondary: #0a4a8a;
        --success: #10b981;
        --warning: #f59e0b;
        --danger: #ef4444;
        --surface: #09090b;
        --surface-panel: #141417;
        --border-subtle: #27272a;
        --text: #fafafa;
        --text-muted: #a1a1aa;
        --text-soft: #71717a;
    }

    html, body, [class*="st-"] {
        font-family: 'IBM Plex Sans', system-ui, -apple-system, sans-serif !important;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'IBM Plex Sans', sans-serif !important;
        color: var(--text) !important;
        letter-spacing: -0.01em;
    }

    /* Page title */
    h1 { font-size: 32px; line-height: 40px; font-weight: 600 !important; }
    h2 { font-size: 24px; line-height: 32px; font-weight: 600 !important; }
    h3 { font-size: 20px; line-height: 28px; font-weight: 500 !important; }
    /* caption under page title */
    h1 + p, .stMarkdown p {
        color: var(--text-muted) !important;
        font-size: 14px !important;
        line-height: 20px !important;
    }

    /* Section header */
    .section-header {
        font-size: 20px; line-height: 28px; font-weight: 500;
        color: var(--text);
        margin-bottom: 8px;
    }

    /* Panel */
    .panel {
        background: var(--surface-panel);
        border: 1px solid var(--border-subtle);
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.3), 0 8px 24px -8px rgba(0,0,0,0.5);
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        border-bottom: 1px solid var(--border-subtle) !important;
        gap: 8px !important;
    }
    .stTabs [data-baseweb="tab"] {
        color: var(--text-muted) !important;
        font-weight: 400 !important;
        font-size: 14px !important;
        padding: 12px 16px !important;
        border-bottom: 2px solid transparent !important;
    }
    .stTabs [aria-selected="true"] {
        color: var(--text) !important;
        font-weight: 600 !important;
    }
    .stTabs [data-baseweb="tab-highlight"] {
        background-color: var(--primary) !important;
        height: 2px !important;
    }

    /* Buttons: primary + secondary */
    .stButton > button, .stDownloadButton > button {
        font-weight: 500 !important;
        font-size: 14px !important;
        height: 40px !important;
        min-width: 44px !important;
        border-radius: 8px !important;
        border: 1px solid var(--border-subtle) !important;
        transition: background-color 150ms ease-out, border-color 150ms ease-out !important;
    }
    .stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {
        background-color: var(--primary) !important;
        border-color: var(--primary) !important;
        color: #ffffff !important;
    }
    .stButton > button[kind="primary"]:hover, .stDownloadButton > button[kind="primary"]:hover {
        background-color: var(--secondary) !important;
        border-color: var(--secondary) !important;
    }
    .stButton > button:disabled, .stDownloadButton > button:disabled {
        background-color: var(--surface-panel) !important;
        color: var(--text-soft) !important;
        border-color: var(--border-subtle) !important;
        cursor: not-allowed !important;
    }

    /* Focus ring */
    .stButton > button:focus-visible,
    .stDownloadButton > button:focus-visible,
    .stTextInput input:focus-visible,
    .stTextArea textarea:focus-visible,
    .stSelectbox [role="combobox"]:focus-visible,
    .stTabs [data-baseweb="tab"]:focus-visible {
        outline: 2px solid var(--primary) !important;
        outline-offset: 2px !important;
        box-shadow: none !important;
    }

    /* Inputs */
    .stTextInput input, .stTextArea textarea, .stSelectbox [data-baseweb="select"] {
        background-color: var(--surface-panel) !important;
        border: 1px solid var(--border-subtle) !important;
        color: var(--text) !important;
        border-radius: 6px !important;
        font-size: 14px !important;
        transition: border-color 150ms ease-out !important;
    }
    .stTextInput input::placeholder, .stTextArea textarea::placeholder {
        color: var(--text-soft) !important;
    }

    /* Sidebar surface */
    [data-testid="stSidebar"] {
        background-color: var(--surface-panel) !important;
        border-right: 1px solid var(--border-subtle) !important;
    }

    /* Data editor / dataframe */
    .stDataFrame, [data-testid="stDataFrame"] {
        border: 1px solid var(--border-subtle);
        border-radius: 8px;
        overflow: hidden;
    }
    .stDataFrame thead { background-color: var(--surface-panel) !important; }
    .stDataFrame th {
        color: var(--text) !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        border-bottom: 1px solid var(--border-subtle) !important;
    }
    .stDataFrame td {
        color: var(--text) !important;
        font-size: 14px !important;
        border-bottom: 1px solid var(--border-subtle) !important;
    }

    /* Status banners (Streamlit st.success/error/warning/info) */
    .stAlert, [data-testid="stAlert"] {
        border-radius: 8px !important;
        border-left-width: 4px !important;
        font-size: 14px !important;
    }

    /* Status caption baseline (rows · cols · size) */
    .stat-caption {
        font-size: 12px;
        line-height: 16px;
        color: var(--text-muted);
        margin-bottom: 8px;
    }

    /* Vertical rhythm */
    .block-margin-32 { margin-top: 32px; margin-bottom: 32px; }
    .block-margin-24 { margin-top: 24px; margin-bottom: 24px; }
    .block-margin-16 { margin-top: 16px; margin-bottom: 16px; }
    .block-margin-8  { margin-top: 8px;  margin-bottom: 8px;  }

    /* Reduced motion */
    @media (prefers-reduced-motion: reduce) {
        * {
            transition-duration: 0.01ms !important;
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
        }
    }
    </style>
    """ )


def apply_enterprise_theme() -> None:
    """Inject the global Stylesheet. Idempotent; safe to call on every rerun."""
    st.markdown(_THEME_CSS, unsafe_allow_html=True)


def section_header(label: str) -> None:
    """Render a 20/28/500 section header (DESIGN.md 'Section header')."""
    st.markdown(f'<div class="section-header">{label}</div>', unsafe_allow_html=True)


def stat_caption(text: str) -> None:
    """Render a 12/16 muted caption (e.g. rows · cols · size)."""
    st.markdown(f'<div class="stat-caption">{text}</div>', unsafe_allow_html=True)


def vertical_space(units: str = "24") -> None:
    """Add a controlled vertical gap (8/16/24/32). Accepts these only."""
    if units not in ("8", "16", "24", "32"):
        raise ValueError("units must be one of 8, 16, 24, 32")
    st.markdown(f'<div class="block-margin-{units}"></div>', unsafe_allow_html=True)