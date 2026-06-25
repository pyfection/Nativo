"""
Shared text tokenisation and match-folding.

Both the auto-link suggester (`document_service`) and the spelling-correction
resolver (`spelling_service`) walk a Text the same way: split it into word
tokens, then fold each token to a diacritic- and case-insensitive key so that
lookups ignore the cosmetic differences a non-standardised orthography produces.

Keeping the tokenizer and the fold in one place guarantees the two pipelines
agree — a token the corrector rewrites to a standard spelling must tokenize
identically when the linker later indexes it.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable

# A token is a run of word characters, apostrophes and hyphens (so "don't" and
# "well-known" stay whole). Unicode-aware so non-Latin scripts tokenize too.
TOKEN_PATTERN = re.compile(r"\b[\w'-]+\b", re.UNICODE)


def fold_for_match(value: str) -> str:
    """Lower-case and strip combining diacritics for index/lookup keys."""
    normalized = unicodedata.normalize("NFD", value or "")
    without_marks = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    return without_marks.casefold()


def iter_tokens(content: str) -> Iterable[tuple[str, int, int]]:
    """Yield (token, start_char, end_char) for every word token in `content`."""
    for match in TOKEN_PATTERN.finditer(content or ""):
        yield match.group(0), match.start(), match.end()
