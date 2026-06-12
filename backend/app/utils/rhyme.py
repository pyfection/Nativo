"""
Rhyme-key derivation from IPA.

A `rhyme_key` is "the last stressed vowel and everything after it" — two words
share a rhyme key iff they (perfect-)rhyme. A `near_rhyme_key` is just the
vowel nucleus, which catches slant/half rhymes.

The implementation is heuristic and intentionally permissive: IPA in this
project is contributed by humans with varying training, so we strip whitespace,
treat the primary stress mark (ˈ) and secondary stress mark (ˌ) as anchors,
fall back to "last vowel onward" when no stress marks are present, and return
None when we can't extract anything useful.

Callers should recompute both keys whenever `WordForm.ipa_pronunciation`
changes — typically in a service-layer setter.
"""
from __future__ import annotations

# IPA vowel inventory — covers the standard chart plus the common diphthong
# components. Length marker (ː) and nasalization (̃) are kept with the vowel.
_IPA_VOWELS = frozenset(
    "aæɐɑɒeɛəɘɜiɪɨoɔøœɵuʊʉyʏʌ"
)
_PRIMARY_STRESS = "ˈ"
_SECONDARY_STRESS = "ˌ"
_SYLLABLE_BREAK = "."


def _strip(ipa: str) -> str:
    return "".join(ipa.split()).strip("/[]")


def compute_rhyme_key(ipa: str | None) -> str | None:
    """
    Return the rhyme key for an IPA string, or None if we can't extract one.

    Algorithm: find the last primary-stress mark; if absent, the last
    secondary-stress mark; if absent, the position of the last vowel. Return
    the substring from that anchor to the end, with stress marks removed.
    """
    if not ipa:
        return None

    cleaned = _strip(ipa)
    if not cleaned:
        return None

    anchor = cleaned.rfind(_PRIMARY_STRESS)
    if anchor == -1:
        anchor = cleaned.rfind(_SECONDARY_STRESS)
    if anchor != -1:
        tail = cleaned[anchor + 1:]
    else:
        # No stress marks — fall back to the last vowel.
        last_vowel = -1
        for i, ch in enumerate(cleaned):
            if ch in _IPA_VOWELS:
                last_vowel = i
        if last_vowel == -1:
            return None
        tail = cleaned[last_vowel:]

    # Drop any embedded stress / syllable-break marks from the tail.
    tail = tail.replace(_PRIMARY_STRESS, "").replace(_SECONDARY_STRESS, "").replace(
        _SYLLABLE_BREAK, ""
    )
    return tail or None


def compute_near_rhyme_key(ipa: str | None) -> str | None:
    """
    Return just the vowel nucleus of the rhyme key — useful for slant rhymes
    where the coda differs but the vowel matches.
    """
    rhyme = compute_rhyme_key(ipa)
    if not rhyme:
        return None
    vowels = "".join(ch for ch in rhyme if ch in _IPA_VOWELS or ch in "ːˑ̃")
    return vowels or None
