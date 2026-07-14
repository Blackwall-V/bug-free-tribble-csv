"""MySQL driver (PyMySQL)."""
from __future__ import annotations

from typing import Any, Dict, List

from .registry import register_driver
from .base import BaseDatabaseDriver, DriverField


@register_driver("MySQL")
class MySQLDriver(BaseDatabaseDriver):
    name = "MySQL"
    supports_table = True
    fields = [
        DriverField("host", "Host", "text", default="localhost"),
        DriverField("port", "Port", "int", default="3306"),
        DriverField("username", "User", "text", default=""),
        DriverField("password", "Password", "password", default=""),
        DriverField("database", "Database name", "text", default="test"),
        DriverField("connection_uri", "Connection URI", "password", default=""),
    ]

    def connect(self):
        import pymysql
        if self.use_uri:
            uri = self.params.get("connection_uri", "")
            if uri.startswith("mysql://"):
                parts = uri[8:].split("@")
                creds = parts[0].split(":")
                host_db = parts[1].split("/")
                user, password = creds[0], creds[1]
                host_port = host_db[0].split(":")
                host = host_port[0]
                port = int(host_port[1]) if len(host_port) > 1 else 3306
                database = host_db[1].split("?")[0]
                return pymysql.connect(host=host, port=port, user=user,
                                       password=password, database=database)
            return pymysql.connect(host=self.params.get("host", "localhost"),
                                   port=int(self.params.get("port") or 3306),
                                   user=self.params.get("username", ""),
                                   password=self.params.get("password", ""),
                                   database=self.params.get("database", ""))
        return pymysql.connect(
            host=self.params.get("host", "localhost"),
            port=int(self.params.get("port") or 3306),
            user=self.params.get("username", ""),
            password=self.params.get("password", ""),
            database=self.params.get("database", ""),
        )

    def prepare_existence(self, conn, target: str, if_exists: str) -> None:
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES LIKE %s", (target,))
        exists = bool(cursor.fetchone())
        if if_exists == "replace" and exists:
            cursor.execute(f"DROP TABLE IF EXISTS {target}")
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