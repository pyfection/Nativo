from dataclasses import dataclass, field

from ._base import Model


@dataclass
class User(Model):
    name: str

    class Meta:
        table_name = "user"
