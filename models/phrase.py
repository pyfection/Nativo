import re
from dataclasses import dataclass, field
from typing import ClassVar

from ._base import Model
from .word import Word


uuid_pattern = r"\{\{([a-z0-9-]{36}):?([tul])?\}\}"
@dataclass
class Phrase(Model):
    raw_text: str
    creator: str
    _words: dict[str: Word] = field(init=False, repr=False, default_factory=dict)
    _modifiers: ClassVar = {
        "": lambda w: w,
        "t": lambda w: w.title(),
        "u": lambda w: w.upper(),
        "l": lambda w: w.lower(),
    }

    class Meta:
        table_name = "phrase"

    @property
    def text(self):
        """Evaluates all word links with actual words from raw_text."""
        text = self.raw_text
        for word_id, modifier in re.findall(uuid_pattern, self.raw_text):
            try:
                word = self._words[word_id]
            except KeyError:
                word = Word.get(word_id)
                self._words[word_id] = word
            if modifier:
                key = f"{{{{{word_id}:{modifier}}}}}"
            else:
                key = f"{{{{{word_id}}}}}"

            modifier = self._modifiers[modifier]
            text = text.replace(key, modifier(word.word))
        return text

    def asdict(self):
        data = super().asdict()
        data.pop("_words")
        return data
