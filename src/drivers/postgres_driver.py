"""PostgreSQL driver (psycopg2)."""
from __future__ import annotations

from typing import Any, Dict, List

from .registry import register_driver
from .base import BaseDatabaseDriver, DriverField


@register_driver("PostgreSQL")
class PostgresDriver(BaseDatabaseDriver):
    name = "PostgreSQL"
    supports_table = True
    fields = [
        DriverField("host", "Host", "text", default="localhost"),
        DriverField("port", "Port", "int", default="5432"),
        DriverField("username", "User", "text", default=""),
        DriverField("password", "Password", "password", default=""),
        DriverField("database", "Database name", "text", default="test"),
        DriverField("connection_uri", "Connection URI", "password", default=""),
    ]

    def connect(self):
        import psycopg2
        if self.use_uri:
            return psycopg2.connect(self.params.get("connection_uri", ""))
        return psycopg2.connect(
            host=self.params.get("host", "localhost"),
            port=int(self.params.get("port") or 5432),
            user=self.params.get("username", ""),
            password=self.params.get("password", ""),
            database=self.params.get("database", ""),
        )

    def prepare_existence(self, conn, target: str, if_exists: str) -> None:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = %s)",
            (target,),
        )
        exists = bool(cursor.fetchone()[0])
        if if_exists == "replace" and exists:
            cursor.execute(f"DROP TABLE IF EXISTS {target} CASCADE")
        elif if_exists == "fail" and exists:
            raise ValueError(f"Table '{target}' already exists.")

    def create_target(self, conn, target: str, schema: Dict[str, Any], if_exists: str) -> None:
        cursor = conn.cursor()
        type_map = {
            "Integer": "INTEGER", "Float": "REAL",
            "Boolean": "BOOLEAN", "Date": "DATE",
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
        placeholders = ", ".join(["%s"] * len(columns))
        insert_sql = f"INSERT INTO {target} ({', '.join(columns)}) VALUES ({placeholders})"
        for row in data:
            cursor.execute(insert_sql, [row.get(c) for c in columns])
        conn.commit()
        return len(data)