"""Abstract database driver interface.

Adding a new target requires three things:

1. Subclass ``BaseDatabaseDriver``.
2. Implement the four abstract methods.
3. Decorate with ``@register_driver("YourDB")`` in your driver file.

That's it — the UI discovers it automatically via ``available_drivers()``.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Type


@dataclass
class DriverField:
    """UI-facing field descriptor for connection configuration."""
    key: str
    label: str
    kind: str = "text"           # "text" | "password" | "int" | "toggle"
    default: str = ""
    required: bool = True


class BaseDatabaseDriver(ABC):
    """Common interface for all database export drivers.

    Subclasses describe their connection inputs via ``fields`` and
    implement the two operations SQL/NoSQL require. They inherit
    ``export`` which orchestrates connect → create_target → insert.
    """
    name: str = "base"
    supports_table: bool = True   # backend has tables with columns
    fields: List[DriverField] = []

    def __init__(self, params: Dict[str, Any], use_uri: bool = False) -> None:
        self.params = params
        self.use_uri = use_uri

    # ---------------- abstract surface ----------------

    @abstractmethod
    def connect(self):
        """Return a live connection object."""

    @abstractmethod
    def create_target(self, conn, target: str, schema: Dict[str, Any], if_exists: str) -> None:
        """Ensure a table/collection exists; behavior depends on if_exists."""

    @abstractmethod
    def insert_rows(self, conn, target: str, schema: Dict[str, Any],
                    data: List[Dict[str, Any]]) -> int:
        """Insert rows; return number of rows written."""

    @abstractmethod
    def prepare_existence(self, conn, target: str, if_exists: str) -> None:
        """Handle the 'replace'/'fail' contract before creating the target."""

    # ---------------- template method ----------------

    def export(self, target: str, schema: Dict[str, Any],
               data: List[Dict[str, Any]], if_exists: str
               ) -> Tuple[bool, str]:
        """Template method: connect → prepare → create → insert.

        Returns ``(success, message)``.
        """
        if not data:
            return True, "No rows to export."
        try:
            conn = self.connect()
            self.prepare_existence(conn, target, if_exists)
            self.create_target(conn, target, schema, if_exists)
            written = self.insert_rows(conn, target, schema, data)
            self.close(conn)
            return True, f"Successfully exported {written} rows to {self.name}."
        except Exception as exc:
            return False, str(exc)

    # ---------------- optional hooks ----------------

    def close(self, conn) -> None:
        """Close the connection. Best-effort; default no-op."""
        try:
            close = getattr(conn, "close", None)
            if callable(close):
                close()
        except Exception:
            pass