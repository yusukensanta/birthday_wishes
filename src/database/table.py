from typing import Any

from schema import And, Schema, SchemaError, Use
from tinydb import TinyDB, where
from tinydb.queries import QueryInstance


class BaseTable:
    def __init__(self):
        client = TinyDB("/tmp/birthday_wishes.json")
        self.table = client.table(type(self).__name__.lower())

    @property
    def _filter_keys(self) -> list[str]:
        # define filter keys in subclass
        return []

    @property
    def _schema(self) -> Schema:
        # define schema in subclass
        return Schema({})

    def filter_conditions(self, data: dict[str, Any]) -> QueryInstance:
        filter = None
        for key in self._filter_keys:
            if not filter:
                filter = where(key) == data.get(key, None)
            else:
                filter = filter & (where(key) == data.get(key, None))

        return filter

    def _has_valid_schema(self, data: dict[str, Any]) -> bool:
        try:
            self._schema.validate(data)
            return True
        except SchemaError:
            return False

    def list_all(self) -> list[dict[str, Any]]:
        return self.table.all()

    def insert(self, data: dict[str, Any]) -> None:
        if self._has_valid_schema(data):
            self.table.insert(data)
        else:
            raise ValueError("Invalid schema")

    def update(self, data: dict[str, Any]) -> None:
        if self._has_valid_schema(data):
            self.table.update(
                data,
                self.filter_conditions(data),
            )
        else:
            raise ValueError("Invalid schema")

    def delete(self, data: dict[str, Any]) -> None:
        self.table.remove(self.filter_conditions(data))

    def search(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        return self.table.search(self.filter_conditions(data))

    def record_exists(self, data: dict[str, Any]) -> bool:
        records = self.search(data)
        if records:
            return True
        else:
            return False


class MemberTable(BaseTable):
    def __init__(self):
        super().__init__()

    @property
    def _filter_keys(self) -> list[str]:
        return ["member_id", "server_id"]

    @property
    def _schema(self) -> Schema:
        return Schema(
            {
                "member_id": And(Use(int)),
                "server_id": And(Use(int)),
                "month": And(Use(int)),
                "day": And(Use(int)),
            }
        )


class ChannelTable(BaseTable):
    def __init__(self):
        super().__init__()

    @property
    def _filter_keys(self) -> list[str]:
        return ["server_id"]

    @property
    def _schema(self) -> Schema:
        return Schema(
            {
                "server_id": And(Use(int)),
                "channel_id": And(Use(int)),
            }
        )
