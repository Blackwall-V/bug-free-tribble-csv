"""Central configuration constants for the CSV AI Generator app."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


APP_TITLE = "AI Data Generator"
APP_CAPTION = "Generate synthetic test datasets using the Groq API."
PAGE_TITLE = "AI CSV Generator"
LAYOUT = "wide"
INITIAL_SIDEBAR_STATE = "expanded"


SUPPORTED_MODELS: List[str] = [
    "llama-3.1-8b-instant",
    "llama-3.3-70b-versatile",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "qwen/qwen3-32b",
]
DEFAULT_MODEL = SUPPORTED_MODELS[0]


BATCH_MIN = 5
BATCH_MAX = 25
BATCH_DEFAULT = 10
BATCH_STEP = 5
BATCH_HELP = "Rows generated per API request. Lower values prevent model truncation."


ROWS_MIN = 5
ROWS_MAX = 1000
ROWS_DEFAULT = 50
ROWS_STEP = 10


SUPPORTED_TYPES = [
    "String", "Integer", "Float", "Date", "Boolean", "Email", "Category"
]

IF_EXISTS_OPTIONS = ["fail", "replace"]
DB_TYPES = ["SQLite", "PostgreSQL", "MySQL", "MongoDB"]


SPACING_SCALE = (4, 8, 12, 16, 24, 32)
COLOR_TOKENS = {
    "primary": "#0C0C09",
    "secondary": "#312C85",
    "success": "#16A34A",
    "warning": "#D97706",
    "danger":  "#DC2626",
    "surface": "#F4F4F1",
    "text":    "#0C0C09",
}


@dataclass
class GenerationConfig:
    """Runtime params bound to a single generate call."""
    api_key: str
    model: str = DEFAULT_MODEL
    batch_size: int = BATCH_DEFAULT
    total_rows: int = ROWS_DEFAULT
    api_type: str = "groq"


@dataclass
class AppConfig:
    """Top-level app display config."""
    title: str = APP_TITLE
    caption: str = APP_CAPTION
    page_title: str = PAGE_TITLE
    layout: str = LAYOUT
    initial_sidebar_state: str = INITIAL_SIDEBAR_STATE
    models: List[str] = field(default_factory=lambda: list(SUPPORTED_MODELS))