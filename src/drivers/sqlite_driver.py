"""SQLite driver. File-based, no external dependency."""
from __future__ import annotations

import sqlite3
from typing import Any, Dict, List

from .registry import register_driver
from .base import BaseDatabaseDriver, DriverField


@register_driver("SQLite")
class SqliteDriver(BaseDatabaseDriver):
    name = "SQLite"
    supports_table = True
    fields = [
        DriverField("sqlite_path", "SQLite file path", "text", default="sqlite.db"),
    ]

    def connect(self):
        path = self.params.get("sqlite_path", "sqlite.db")
        return sqlite3.connect(path)

    def prepare_existence(self, conn, target: str, if_exists: str) -> None:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (target,),
        )
        exists = bool(cursor.fetchone())
        if if_exists == "replace" and exists:
            cursor.execute(f"DROP TABLE IF EXISTS {target}")
        elif if_exists == "fail" and exists:
            raise ValueError(f"Table '{target}' already exists.")

    def create_target(self, conn, target: str, schema: Dict[str, Any], if_exists: str) -> None:
        cursor = conn.cursor()
        type_map = {
            "Integer": "INTEGER", "Float": "REAL",
            "Boolean": "INTEGER", "Date": "TEXT",
        }
        cols_sql = []
        for col in schema.get("columns", []):
            col_type = type_map.get(col.get("type"), "VARCHAR(255)")
            cols_sql.append(f"{col['name']} {col_type}")
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {target} ({', '.join(cols_sql)})")
        conn.commit()

    def insert_rows(self, conn, target: str, schema: Dict[str, Any],
                    data: List[Dict[str, Any]]) -> int:
        cursor = conn.cursor()
        columns = [col["name"] for col in schema.get("columns", [])]
        placeholders = ", ".join(["?"] * len(columns))
        insert_sql = f"INSERT INTO {target} ({', '.join(columns)}) VALUES ({placeholders})"
        for row in data:
            cursor.execute(insert_sql, [row.get(c) for c in columns])
        conn.commit()
        return len(data)