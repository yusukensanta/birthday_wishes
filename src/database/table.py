from typing import Any

from schema import And, Schema, SchemaError, Use
from tinydb import Query, TinyDB


class UserTable:
    SCHEMA = Schema(
        {
            "id": And(Use(int)),
            "server_id": And(Use(int)),
            "month": And(Use(int)),
            "day": And(Use(int)),
        }
    )

    def __init__(self, db_path: str):
        self.client = TinyDB(db_path)
        self.client.truncate()
        self.table = Query()
        self.primary_key = "id"
        self.secondary_key = "server_id"

    def _has_valid_schema(self, data: dict[str, Any]) -> bool:
        try:
            self.SCHEMA.validate(data)
            return True
        except SchemaError:
            return False

    def insert(self, data: dict[str, Any]) -> None:
        if self._has_valid_schema(data):
            self.client.insert(data)
        else:
            raise ValueError("Invalid schema")

    def update(self, data: dict[str, Any]) -> None:
        if self._has_valid_schema(data):
            self.client.update(
                data,
                (self.table.id == data[self.primary_key])
                & (self.table.server_id == data[self.secondary_key]),
            )
        else:
            raise ValueError("Invalid schema")

    def search(self, record: dict[str, Any]) -> list[dict[str, Any]]:
        return self.client.search(
            self.table.id == record[self.primary_key]
            and self.table.server_id == record[self.secondary_key]
        )

    def record_exists(self, record: dict[str, Any]) -> bool:
        records = self.search(record)
        if records:
            return True
        else:
            return False
