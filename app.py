"""Streamlit entrypoint.

Run with: ``streamlit run app.py``

The whole UI lives in ``src.ui``; this file just loads config and
hands control to ``render_app``. Keeping app.py tiny means the
UI can be tested/replaced without touching the Streamlit runner.
"""
from src.ui import render_app


if __name__ == "__main__":
    render_app()