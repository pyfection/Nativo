import os
from abc import ABC
from dataclasses import dataclass, asdict, field
from datetime import datetime
from uuid import uuid4

from tinydb import TinyDB, Query

db = TinyDB(f"dbs/{os.getenv('NATIVO_LANG')}.json")


@dataclass(kw_only=True)
class Model(ABC):
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(
        default_factory=lambda: datetime.utcnow().isoformat())

    class Meta:
        table_name: str = None

    @classmethod
    def get(cls, id) -> "Model":
        data = db.table(cls.Meta.table_name).search(Query().id == id)[0]
        model = cls(**data)
        return model

    @classmethod
    def all(cls):
        return (cls(**data) for data in db.table(cls.Meta.table_name).all())

    @classmethod
    def clear(cls):
        db.table(cls.Meta.table_name).truncate()

    def commit(self):
        db.table(self.Meta.table_name).insert(asdict(self))
