"""MongoDB driver (pymongo). NoSQL collection-based, not table-based."""
from __future__ import annotations

from typing import Any, Dict, List

from .registry import register_driver
from .base import BaseDatabaseDriver, DriverField


@register_driver("MongoDB")
class MongoDBDriver(BaseDatabaseDriver):
    name = "MongoDB"
    supports_table = False
    fields = [
        DriverField("host", "Host", "text", default="localhost"),
        DriverField("port", "Port", "int", default="27017"),
        DriverField("username", "User", "text", default="", required=False),
        DriverField("password", "Password", "password", default="", required=False),
        DriverField("connection_uri", "Mongo URI", "password", default=""),
        DriverField("database", "Database name", "text", default="test"),
    ]

    def connect(self):
        import pymongo
        if self.use_uri:
            return pymongo.MongoClient(self.params.get("connection_uri", ""))
        host = self.params.get("host", "localhost")
        port = int(self.params.get("port") or 27017)
        user = self.params.get("username", "")
        pwd = self.params.get("password", "")
        return pymongo.MongoClient(
            host=host, port=port,
            username=user or None, password=pwd or None,
        )

    def prepare_existence(self, conn, target: str, if_exists: str) -> None:
        db_name = self.params.get("database", "test")
        collection = conn[db_name][target]
        if if_exists == "replace":
            collection.delete_many({})
        elif if_exists == "fail" and collection.count_documents({}) > 0:
            raise ValueError(f"Collection '{target}' already exists and contains data.")

    def create_target(self, conn, target: str, schema: Dict[str, Any], if_exists: str) -> None:
        # MongoDB collections are schema-less; nothing to pre-create.
        return None

    def insert_rows(self, conn, target: str, schema: Dict[str, Any],
                    data: List[Dict[str, Any]]) -> int:
        db_name = self.params.get("database", "test")
        collection = conn[db_name][target]
        if data:
            collection.insert_many(data)
        return len(data)