"""Schema suggestion and synthetic data generation via the Groq API.

Classes
-------
SchemaGenerator  -- produces a dataset schema dict from a natural-language prompt.
DataGenerator    -- produces list[dict] rows conforming to a schema, in batches.

Logging is reconfigured to use UTF-8 streams so non-ASCII prompts (café, naïve)
do not raise ``'ascii' codec can't encode character`` errors.
"""
from __future__ import annotations

import json
import logging
import sys
from typing import Any, Callable, Dict, List, Optional

from groq import Groq

from .config import DEFAULT_MODEL
from .prompts import (
    DATA_GENERATION_SYSTEM_PROMPT,
    DATA_GENERATION_USER_PROMPT,
    SCHEMA_SYSTEM_PROMPT,
    SCHEMA_USER_PROMPT,
)


def _ensure_utf8_streams() -> None:
    """Force stdout/stderr/logging streams to UTF-8 (errors replaced).

    Streamlit / some launchers attach ASCII pipes; without this, logging a
    prompt containing é/ç/è raises UnicodeEncodeError.
    """
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass
    root = logging.getLogger()
    for handler in root.handlers:
        stream = getattr(handler, "stream", None)
        if stream is not None and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


_ensure_utf8_streams()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SchemaGenerator:
    """Suggest a tabular schema from a natural-language dataset prompt."""

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL) -> None:
        self.client = Groq(api_key=api_key)
        self.model = model

    def suggest(self, user_prompt: str) -> Dict[str, Any]:
        """Return the Groq-suggested schema as a parsed JSON dict.

        Raises
        ------
        ValueError
            If the model returns invalid JSON or an empty response.
        """
        logger.info("Generating schema for %r using %s", user_prompt, self.model)
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SCHEMA_SYSTEM_PROMPT},
                {"role": "user", "content": SCHEMA_USER_PROMPT.format(prompt=user_prompt)},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        content = completion.choices[0].message.content
        if not content:
            raise ValueError("Schema model returned an empty response.")
        return json.loads(content)


class DataGenerator:
    """Generate synthetic rows conforming to a schema in batched calls."""

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL) -> None:
        self.client = Groq(api_key=api_key)
        self.model = model

    def generate_batch(
        self,
        schema: Dict[str, Any],
        row_count: int,
        existing_data: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """Generate a single batch of ``row_count`` rows."""
        exclude_context: str = "None"
        if existing_data:
            exclude_context = json.dumps(existing_data[-15:], indent=2)

        schema_json = json.dumps(schema.get("columns", []), indent=2)
        schema_desc = schema.get("description", "No description provided")

        logger.info("Generating batch of %d rows (model=%s)", row_count, self.model)
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": DATA_GENERATION_SYSTEM_PROMPT.format(row_count=row_count),
                },
                {
                    "role": "user",
                    "content": DATA_GENERATION_USER_PROMPT.format(
                        schema_description=schema_desc,
                        schema_json=schema_json,
                        row_count=row_count,
                        exclude_context=exclude_context,
                    ),
                },
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
        )
        content = completion.choices[0].message.content
        response = json.loads(content) if content else {}
        return response.get("data", [])

    def generate_all(
        self,
        schema: Dict[str, Any],
        total_rows: int,
        batch_size: int = 10,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> List[Dict[str, Any]]:
        """Generate ``total_rows`` rows in batches and return cleaned rows.

        Rows are cleaned to contain only the schema column names, missing
        keys default to None.
        """
        all_rows: List[Dict[str, Any]] = []
        remaining = total_rows

        while remaining > 0:
            current_batch = min(batch_size, remaining)
            try:
                batch = self.generate_batch(schema, current_batch, all_rows)
            except Exception as exc:
                logger.error("Batch generation failed: %s", exc)
                if all_rows:
                    logger.warning("Returning partial dataset (%d rows).", len(all_rows))
                    break
                raise

            if not batch:
                logger.warning("Empty batch; retrying once.")
                batch = self.generate_batch(schema, current_batch, all_rows)
                if not batch:
                    logger.error("LLM returned 0 rows twice. Aborting.")
                    break

            all_rows.extend(batch)
            remaining -= len(batch)
            if progress_callback:
                progress_callback(len(all_rows), total_rows)

        return self._clean_rows(all_rows, schema)

    @staticmethod
    def _clean_rows(
        rows: List[Dict[str, Any]], schema: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        valid_columns = [col["name"] for col in schema.get("columns", [])]
        return [{col: row.get(col) for col in valid_columns} for row in rows]