"""Top-level page shell: page config, title, sidebar, tab routing.

Keeps app.py a one-line entrypoint so the whole UI can be replaced or
unit-tested without touching Streamlit runner concerns.
"""
from __future__ import annotations

import os

import streamlit as st
from dotenv import load_dotenv

from ..config import AppConfig
from .tabs.schema_tab import render_schema_tab
from .tabs.generate_tab import render_generate_tab


def render_app(config: AppConfig | None = None) -> None:
    """Render the full application shell."""
    config = config or AppConfig()
    load_dotenv()

    st.set_page_config(
        page_title=config.page_title,
        layout=config.layout,
        initial_sidebar_state=config.initial_sidebar_state,
    )

    _init_state()

    st.title(config.title)
    st.caption(config.caption)

    api_key, model, batch_size = _render_sidebar(config)

    tab_schema, tab_generate = st.tabs(["Schema Design", "Data Generation"])

    with tab_schema:
        render_schema_tab(api_key=api_key, model=model)

    with tab_generate:
        render_generate_tab(api_key=api_key, model=model, batch_size=batch_size)


def _init_state() -> None:
    st.session_state.setdefault("schema", None)
    st.session_state.setdefault("data", None)
    st.session_state.setdefault("last_prompt", "")


def _render_sidebar(config: AppConfig) -> tuple[str, str, int]:
    st.sidebar.markdown("### Settings")

    default_api_key = os.getenv("GROQ_API_KEY", "")
    api_key = st.sidebar.text_input("Groq API Key", type="password", value=default_api_key)

    model = st.sidebar.selectbox("Model", config.models, index=0)

    batch_size = st.sidebar.slider(
        "Batch size",
        min_value=5, max_value=25, value=10, step=5,
        help="Rows generated per API request. Lower values prevent model truncation.",
    )

    if not api_key:
        st.info("Enter your Groq API Key in the sidebar to begin.")

    return api_key, model, batch_size