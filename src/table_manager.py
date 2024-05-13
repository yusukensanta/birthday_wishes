from typing import Any, Union

from tinydb import TinyDB, where
from tinydb.queries import QueryInstance

from src.model import Birthday, BirthdayChannel


class BaseManager:
    def __init__(self):
        client = TinyDB("/tmp/birthday_wishes.json")
        self.table = client.table(type(self).__name__.lower())

    @property
    def _filter_keys(self) -> list[str]:
        # define filter keys in subclass
        return []

    def filter_conditions(
        self, data: Union[Birthday, BirthdayChannel]
    ) -> QueryInstance:
        filter = None
        for key in self._filter_keys:
            if not filter:
                filter = where(key) == data.dict().get(key, None)
            else:
                filter = filter & (where(key) == data.dict().get(key, None))

        return filter

    def list_all(self, server_id: int) -> list[dict[str, Any]]:
        return self.table.search(where("server_id") == server_id)

    def insert(self, data: Union[Birthday, BirthdayChannel]) -> None:
        self.table.insert(data.dict())

    def update(self, data: Union[Birthday, BirthdayChannel]) -> None:
        self.table.update(
            data.dict(),
            self.filter_conditions(data),
        )

    def delete(self, data: Union[Birthday, BirthdayChannel]) -> None:
        self.table.remove(self.filter_conditions(data))

    def search(
        self, data: Union[Birthday, BirthdayChannel]
    ) -> list[dict[str, Any]]:
        return self.table.search(self.filter_conditions(data))

    def record_exists(self, data: Union[Birthday, BirthdayChannel]) -> bool:
        records = self.search(data)
        if records:
            return True
        else:
            return False


class BirthdayManager(BaseManager):
    def __init__(self):
        super().__init__()

    @property
    def _filter_keys(self) -> list[str]:
        return ["server_id"]


class ChannelManager(BaseManager):
    def __init__(self):
        super().__init__()

    @property
    def _filter_keys(self) -> list[str]:
        return ["server_id"]
