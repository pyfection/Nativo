"""
IPA parsing, phonetic distance, and a rule-based IPA → spelling fallback.

Used by `transcription_service` to turn a phoneme stream (typed IPA or the
output of a phoneme recogniser) into standard spelling. Three pieces:

- `segments` — split an IPA string into comparable phone segments. Matching is
  deliberately coarse: stress, syllable breaks, length and diacritics are
  dropped, because the orthography doesn't encode them (see CLAUDE.md, "Spelling
  is intentionally phonemically underspecified") and recogniser output is noisy
  on exactly those details anyway.
- `sub_cost` / `indel_cost` — a feature-based weighted edit distance, so a near
  miss (ɛ for e, p for b) costs much less than an unrelated phone.
- `spell_segments` — a letter-level fallback for words not in the lexicon. The
  table is a starting point for the Bavarian standard, meant to be refined by
  the language's editors, not a finished orthography. Lexicon matches always
  win over it, so it only shapes words the dictionary doesn't have yet.
"""

from __future__ import annotations

import unicodedata

# Characters that carry no segmental information for matching.
_IGNORED = frozenset("ˈˌ.ːˑ‿|‖/[]()‹›͜͡ʰʲʷˠˤʼˀ̚-'’")

# Spelling/recogniser variants folded onto one canonical symbol.
_CANONICAL = {
    "g": "ɡ",
    "ʌ": "a",  # identical to a for Bavarian ears (native-speaker check)
    "ʀ": "r",
    "ʁ": "r",
    "ɾ": "r",
    "ɹ": "r",
    "ɫ": "l",
    "ɱ": "m",
    "ɕ": "ʃ",
    "ʂ": "ʃ",
    "ʑ": "ʒ",
    "ʐ": "ʒ",
}

# Vowels: (height 0=close … 6=open, backness 0=front … 2=back, rounded).
_VOWELS: dict[str, tuple[int, int, int]] = {
    "i": (0, 0, 0),
    "y": (0, 0, 1),
    "ɨ": (0, 1, 0),
    "ʉ": (0, 1, 1),
    "ɯ": (0, 2, 0),
    "u": (0, 2, 1),
    "ɪ": (1, 0, 0),
    "ʏ": (1, 0, 1),
    "ʊ": (1, 2, 1),
    "e": (2, 0, 0),
    "ø": (2, 0, 1),
    "ɘ": (2, 1, 0),
    "ɵ": (2, 1, 1),
    "o": (2, 2, 1),
    "ə": (3, 1, 0),
    "ɛ": (4, 0, 0),
    "œ": (4, 0, 1),
    "ɜ": (4, 1, 0),
    "ʌ": (4, 2, 0),
    "ɔ": (4, 2, 1),
    "æ": (5, 0, 0),
    "ɐ": (5, 1, 0),
    "a": (6, 0, 0),
    "ɑ": (6, 2, 0),
    "ɒ": (6, 2, 1),
}

# Consonants: (place, manner, voiced). Place/manner are coarse class labels.
_CONSONANTS: dict[str, tuple[str, str, int]] = {
    "p": ("lab", "stop", 0),
    "b": ("lab", "stop", 1),
    "t": ("alv", "stop", 0),
    "d": ("alv", "stop", 1),
    "k": ("vel", "stop", 0),
    "ɡ": ("vel", "stop", 1),
    "q": ("uvu", "stop", 0),
    "ʔ": ("glot", "stop", 0),
    "m": ("lab", "nasal", 1),
    "n": ("alv", "nasal", 1),
    "ɲ": ("pal", "nasal", 1),
    "ŋ": ("vel", "nasal", 1),
    "f": ("lab", "fric", 0),
    "v": ("lab", "fric", 1),
    "β": ("lab", "fric", 1),
    "ʋ": ("lab", "approx", 1),
    "θ": ("dent", "fric", 0),
    "ð": ("dent", "fric", 1),
    "s": ("alv", "fric", 0),
    "z": ("alv", "fric", 1),
    "ʃ": ("post", "fric", 0),
    "ʒ": ("post", "fric", 1),
    "ç": ("pal", "fric", 0),
    "ʝ": ("pal", "fric", 1),
    "x": ("vel", "fric", 0),
    "ɣ": ("vel", "fric", 1),
    "χ": ("uvu", "fric", 0),
    "h": ("glot", "fric", 0),
    "ɦ": ("glot", "fric", 1),
    "j": ("pal", "approx", 1),
    "w": ("lab", "approx", 1),
    "l": ("alv", "lateral", 1),
    "ʎ": ("pal", "lateral", 1),
    "r": ("alv", "rhotic", 1),
}

# Weak vowels that recognisers and speakers drop or insert freely.
_WEAK_VOWELS = frozenset("əɐ")


def segments(ipa: str | None) -> tuple[str, ...]:
    """
    Split IPA into canonical phone segments, one base symbol each.

    Whitespace and punctuation are ignored: word boundaries are recovered by the lexicon search,
    not trusted from the input (recognisers emit space-separated phones).
    """
    if not ipa:
        return ()
    out: list[str] = []
    # NFD splits ç into c + cedilla; put it back so it survives mark-stripping.
    decomposed = unicodedata.normalize("NFD", ipa).replace("c\u0327", "ç")
    for ch in decomposed:
        category = unicodedata.category(ch)
        if ch.isspace() or ch in _IGNORED or category in ("Mn", "Lm") or category[0] == "P":
            continue
        ch = _CANONICAL.get(ch.lower(), ch.lower())
        # A doubled consonant ("haid so" heard as "haɪ t ts uː") is one sound;
        # neighbouring words may share it (see transcription_service).
        if out and out[-1] == ch and ch not in _VOWELS:
            continue
        out.append(ch)
    return tuple(out)


def is_vowel(seg: str) -> bool:
    return seg in _VOWELS


def indel_cost(seg: str) -> float:
    # Vowels in a sequence get merged or dropped in fast speech and by the
    # recogniser (oa heard as a long oː), so losing a vowel costs less than
    # losing a consonant.
    if seg in _WEAK_VOWELS:
        return 0.5
    return 0.7 if seg in _VOWELS else 1.0


def sub_cost(a: str, b: str) -> float:
    if a == b:
        return 0.0
    va, vb = _VOWELS.get(a), _VOWELS.get(b)
    if va and vb and "ə" in (a, b):
        # ə is the reduced form of any vowel in quick, unstressed words
        # ("di" heard as "tə").
        return 0.25
    if va and vb:
        cost = 0.15 + 0.08 * abs(va[0] - vb[0]) + 0.15 * abs(va[1] - vb[1])
        cost += 0.15 * (va[2] != vb[2])
        return min(cost, 0.8)
    ca, cb = _CONSONANTS.get(a), _CONSONANTS.get(b)
    if ca and cb:
        same_place, same_manner = ca[0] == cb[0], ca[1] == cb[1]
        if same_place and same_manner:
            return 0.25  # voicing only — Bavarian lenis/fortis is often unclear
        if same_place or same_manner:
            return 0.6
        return 0.9
    # Glide ↔ high vowel (j/i, w/u) are near neighbours.
    if {a, b} in ({"j", "i"}, {"w", "u"}, {"v", "u"}):
        return 0.5
    return 1.0


# ---------------------------------------------------------------------------
# Spelling fallback for out-of-lexicon words
# ---------------------------------------------------------------------------

# One letter (or letter group) per sound, agreed with a native speaker. Vowel
# sequences are not special — "diphthongs" are just two vowels written in a row
# (ia, iá, io are all distinct words). Lenis/fortis stays as heard: d+s → ds,
# t+s → ts. Sounds Bavarian doesn't use are still listed, mapped to the nearest
# letter, because the multilingual recogniser emits them anyway. Length and
# stress are never written.
_SPELLING_RULES: dict[tuple[str, ...], str] = {
    ("ŋ", "k"): "nk",
    # Vowels
    ("a",): "a",
    ("ɐ",): "á",
    ("ɑ",): "á",
    ("e",): "e",
    ("ɛ",): "é",
    ("æ",): "é",
    ("i",): "i",
    ("ɪ",): "i",
    ("o",): "o",
    ("ɔ",): "ó",
    ("ɒ",): "ó",
    ("u",): "u",
    ("ʊ",): "u",
    # Reduced vowel of quick, unstressed words (di = [də]); conventionally i.
    ("ə",): "i",
    # Not used in Bavarian — nearest letter
    ("ø",): "é",
    ("œ",): "é",
    ("y",): "i",
    ("ʏ",): "i",
    ("ɨ",): "i",
    ("ʉ",): "u",
    ("ɯ",): "u",
    ("ɘ",): "e",
    ("ɵ",): "o",
    ("ɜ",): "é",
    # Consonants
    ("ʃ",): "c",
    ("ʒ",): "c",
    ("x",): "x",
    ("ŋ",): "ng",
    ("z",): "s",
    ("ɡ",): "g",
    ("ʔ",): "",
    # Not used in Bavarian — nearest letter
    ("ç",): "x",
    ("χ",): "x",
    ("ɣ",): "g",
    ("j",): "i",
    ("ʝ",): "i",
    ("w",): "v",
    ("ʋ",): "v",
    ("β",): "v",
    ("ɦ",): "h",
    ("θ",): "s",
    ("ð",): "d",
    ("ɲ",): "n",
    ("ʎ",): "l",
    ("q",): "k",
}
_MAX_RULE_LEN = max(len(k) for k in _SPELLING_RULES)


def spell_segments(segs: tuple[str, ...]) -> str:
    """Greedy longest-match IPA → letters, for words the lexicon doesn't know."""
    out: list[str] = []
    i = 0
    while i < len(segs):
        for size in range(min(_MAX_RULE_LEN, len(segs) - i), 0, -1):
            chunk = segs[i : i + size]
            if chunk in _SPELLING_RULES:
                out.append(_SPELLING_RULES[chunk])
                i += size
                break
        else:
            out.append(segs[i])
            i += 1
    return "".join(out)
