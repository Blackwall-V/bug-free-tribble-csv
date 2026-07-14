"""src package root.

Re-exporting key public symbols for ergonomic imports like
``from src import SchemaGenerator, DataGenerator, drivers``.
"""
from .config import AppConfig, GenerationConfig
from .generator import SchemaGenerator, DataGenerator
from .prompts import (
    SCHEMA_SYSTEM_PROMPT, SCHEMA_USER_PROMPT,
    DATA_GENERATION_SYSTEM_PROMPT, DATA_GENERATION_USER_PROMPT,
)
from . import drivers

__all__ = [
    "AppConfig", "GenerationConfig",
    "SchemaGenerator", "DataGenerator",
    "SCHEMA_SYSTEM_PROMPT", "SCHEMA_USER_PROMPT",
    "DATA_GENERATION_SYSTEM_PROMPT", "DATA_GENERATION_USER_PROMPT",
    "drivers",
]