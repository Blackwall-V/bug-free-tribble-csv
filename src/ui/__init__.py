"""UI package for the CSV AI Generator app.

Each module renders one logical section of the page. The package
exposes a single ``render_app()`` entrypoint used by app.py.
"""
from .app_shell import render_app

__all__ = ["render_app"]