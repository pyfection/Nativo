from dataclasses import dataclass, field

from ._base import Model


@dataclass
class Word(Model):
    word: str
    tags: list[str] = field(default_factory=list)
    description: str = ""
    # language: description
    foreign_description: dict[str, str] = field(default_factory=dict)
    word_base: str = None  # ID

    class Meta:
        table_name = "word"

    @property
    def base_word(self) -> "Word":
        return Word.get(self.word_base)
