"""UI package for the CSV AI Generator app.

Each module renders one logical section of the page. The package
exposes a single ``render_app()`` entrypoint used by app.py.
"""
from .app_shell import render_app
from .styles import apply_enterprise_theme, section_header, stat_caption, vertical_space

__all__ = [
    "render_app",
    "apply_enterprise_theme", "section_header", "stat_caption", "vertical_space",
]