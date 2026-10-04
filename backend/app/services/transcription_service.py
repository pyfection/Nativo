"""
Speech / IPA → standard spelling.

Pipeline (phase 1 of the speech-to-standard tool):

1. Audio → IPA via a zero-shot phoneme recogniser (`app.utils.phoneme_recognizer`).
2. IPA → words: the phone stream has no word boundaries, so we search for the
   cheapest split into lexicon words. Every `WordForm` with an
   `ipa_pronunciation` is a candidate; spans are matched with a weighted
   phonetic edit distance (`app.utils.ipa`), walked over a trie so shared
   prefixes are scored once.
3. Words → spelling: a matched span takes its WordForm's `form` (the standard
   spelling by definition). Spans nothing matches are spelled by the rule-based
   fallback and flagged `known=False`.

Like `spelling_service`, this is suggest-only: it returns candidates per token
and never writes anything.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy.orm import Session, contains_eager

from app.models.word import Lexeme, LexemeStatus, WordForm
from app.schemas.transcription import (
    TranscriptionCandidate,
    TranscriptionResult,
    TranscriptionToken,
)
from app.utils import phoneme_recognizer
from app.utils.ipa import indel_cost, is_vowel, segments, spell_segments, sub_cost

# Segmentation costs. A matched word costs its phonetic distance + WORD_COST
# (so the search doesn't shatter the input into many tiny words); an unmatched
# segment costs UNKNOWN_COST, a bit more than one full substitution.
WORD_COST = 0.4
UNKNOWN_COST = 1.2
# Fast speech merges a consonant shared across a word boundary ("is so" said as
# "isso"); a word may reuse the previous word's last consonant for this cost.
SHARED_SOUND_COST = 0.1
# Candidates within this distance of the best match are offered as alternatives.
CANDIDATE_SLACK = 0.35
MAX_CANDIDATES = 5

# Multiple pronunciations in one IPA field, e.g. "ˈhɔːb, hɔb".
_IPA_ALTERNATIVES = re.compile(r"[,;~]")


def _max_distance(length: int) -> float:
    """How far a span may drift from a word of `length` segments and still match."""
    return max(0.5, 0.34 * length)


@dataclass
class _Node:
    children: dict[str, _Node] = field(default_factory=dict)
    forms: list[WordForm] = field(default_factory=list)
    max_len_below: int = 0


@dataclass
class _Lexicon:
    root: _Node
    max_len: int
    size: int


def _build_lexicon(word_forms: list[WordForm]) -> _Lexicon:
    root = _Node()
    max_len = 0
    for wf in word_forms:
        for alternative in _IPA_ALTERNATIVES.split(wf.ipa_pronunciation or ""):
            segs = segments(alternative)
            if not segs:
                continue
            max_len = max(max_len, len(segs))
            node = root
            node.max_len_below = max(node.max_len_below, len(segs))
            for seg in segs:
                node = node.children.setdefault(seg, _Node())
                node.max_len_below = max(node.max_len_below, len(segs))
            if wf not in node.forms:
                node.forms.append(wf)
    return _Lexicon(root=root, max_len=max_len, size=len(word_forms))


def _load_lexicon(db: Session, language_id: UUID) -> _Lexicon:
    word_forms = (
        db.query(WordForm)
        .join(Lexeme, Lexeme.id == WordForm.lexeme_id)
        .options(contains_eager(WordForm.lexeme))
        .filter(
            Lexeme.language_id == language_id,
            Lexeme.status == LexemeStatus.PUBLISHED,
            WordForm.ipa_pronunciation.isnot(None),
            WordForm.ipa_pronunciation != "",
        )
        .all()
    )
    return _build_lexicon(word_forms)


def _matches_from(
    root: _Node, query: tuple[str, ...], depth: int = 0
) -> list[tuple[int, float, WordForm]]:
    """
    Every lexicon word that matches a prefix of `query` closely enough, as
    (prefix_length, distance, word_form). One Levenshtein row per trie node:
    row[k] is the distance between the node's path and query[:k].
    """
    first_row = [0.0]
    for seg in query:
        first_row.append(first_row[-1] + indel_cost(seg))

    results: list[tuple[int, float, WordForm]] = []
    stack: list[tuple[_Node, list[float], int]] = [(root, first_row, depth)]
    while stack:
        node, prev, depth = stack.pop()
        for seg, child in node.children.items():
            row = [prev[0] + indel_cost(seg)]
            for k, q in enumerate(query, start=1):
                row.append(
                    min(
                        prev[k] + indel_cost(seg),
                        row[k - 1] + indel_cost(q),
                        prev[k - 1] + sub_cost(seg, q),
                    )
                )
            child_depth = depth + 1
            if child.forms:
                limit = _max_distance(child_depth)
                for k in range(1, len(row)):
                    if row[k] <= limit:
                        results.extend((k, row[k], wf) for wf in child.forms)
            # Row minima never decrease with depth, so this prune is safe.
            if min(row) <= _max_distance(child.max_len_below):
                stack.append((child, row, child_depth))
    return results


def _candidate(wf: WordForm, distance: float) -> TranscriptionCandidate:
    return TranscriptionCandidate(
        word_form_id=wf.id,
        lexeme_id=wf.lexeme_id,
        form=wf.form,
        lemma=wf.lexeme.lemma if wf.lexeme else wf.form,
        ipa_pronunciation=wf.ipa_pronunciation or "",
        distance=round(distance, 3),
    )


def _word_token(span: tuple[str, ...], matches: list[tuple[float, WordForm]]) -> TranscriptionToken:
    # Ties (e.g. ɪs fits "es" and "is" equally) go to the word spelled the way
    # the letter rules would spell what was heard, then lemmas, then A–Z.
    heard = spell_segments(span).casefold()
    matches = sorted(
        matches,
        key=lambda m: (round(m[0], 6), m[1].form.casefold() != heard, not m[1].is_lemma, m[1].form),
    )
    best_distance = matches[0][0]
    seen: set[UUID] = set()
    candidates: list[TranscriptionCandidate] = []
    for distance, wf in matches:
        if distance > best_distance + CANDIDATE_SLACK or len(candidates) >= MAX_CANDIDATES:
            break
        if wf.id in seen:
            continue
        seen.add(wf.id)
        candidates.append(_candidate(wf, distance))

    # Exact (case-insensitive) compare: accents are contrastive here (a vs á).
    best_spelling = candidates[0].form.casefold()
    return TranscriptionToken(
        ipa="".join(span),
        spelling=candidates[0].form,
        known=True,
        ambiguous=any(c.form.casefold() != best_spelling for c in candidates),
        confidence=round(max(0.0, 1.0 - best_distance / len(span)), 2),
        candidates=candidates,
    )


def _unknown_token(span: tuple[str, ...]) -> TranscriptionToken:
    return TranscriptionToken(
        ipa="".join(span),
        spelling=spell_segments(span),
        known=False,
        ambiguous=False,
        confidence=0.0,
        candidates=[],
    )


def transcribe_segments(segs: tuple[str, ...], lexicon: _Lexicon) -> list[TranscriptionToken]:
    """Cheapest split of `segs` into lexicon words and unknown stretches."""
    n = len(segs)
    best = [float("inf")] * (n + 1)
    # back[end] = (previous state, start of the span in segs, is_word). The two
    # differ only when a word reuses the previous word's last sound.
    back: list[tuple[int, int, bool]] = [(0, 0, False)] * (n + 1)
    best[0] = 0.0
    spans: dict[tuple[int, int], list[tuple[float, WordForm]]] = defaultdict(list)
    window = lexicon.max_len + 3

    for start in range(n):
        if best[start] + UNKNOWN_COST < best[start + 1]:
            best[start + 1] = best[start] + UNKNOWN_COST
            back[start + 1] = (start, start, False)
        if not lexicon.size:
            continue
        query = segs[start : start + window]
        for length, distance, wf in _matches_from(lexicon.root, query):
            end = start + length
            spans[(start, end)].append((distance, wf))
            cost = best[start] + distance + WORD_COST
            if cost < best[end]:
                best[end] = cost
                back[end] = (start, start, True)

        # Words starting with the consonant the previous word ended on.
        shared = segs[start - 1] if start and back[start][2] else None
        if shared and not is_vowel(shared) and shared in lexicon.root.children:
            subtree = lexicon.root.children[shared]
            for length, distance, wf in _matches_from(subtree, query, depth=1):
                end = start + length
                spans[(start - 1, end)].append((distance, wf))
                cost = best[start] + distance + WORD_COST + SHARED_SOUND_COST
                if cost < best[end]:
                    best[end] = cost
                    back[end] = (start, start - 1, True)

    # Walk back, then merge adjacent unknown segments into one token.
    pieces: list[tuple[int, int, int, bool]] = []
    end = n
    while end > 0:
        state, span_start, is_word = back[end]
        pieces.append((state, span_start, end, is_word))
        end = state
    pieces.reverse()

    tokens: list[TranscriptionToken] = []
    unknown_start: int | None = None
    for state, span_start, end, is_word in pieces:
        if not is_word:
            if unknown_start is None:
                unknown_start = state
            continue
        if unknown_start is not None:
            tokens.append(_unknown_token(segs[unknown_start:state]))
            unknown_start = None
        tokens.append(_word_token(segs[span_start:end], spans[(span_start, end)]))
    if unknown_start is not None:
        tokens.append(_unknown_token(segs[unknown_start:n]))
    return tokens


def _capitalize_first(tokens: list[TranscriptionToken]) -> None:
    """
    Only the first word and personal names are capitalised. Names keep the case
    stored on their dictionary entry; nothing else is touched (no
    str.capitalize, which would lower-case the rest of the word).
    """
    for token in tokens:
        if token.spelling:
            token.spelling = token.spelling[0].upper() + token.spelling[1:]
            return


def transcribe_ipa(db: Session, language_id: UUID, ipa: str) -> TranscriptionResult:
    lexicon = _load_lexicon(db, language_id)
    tokens = transcribe_segments(segments(ipa), lexicon)
    _capitalize_first(tokens)
    return TranscriptionResult(
        ipa=ipa,
        text=" ".join(t.spelling for t in tokens if t.spelling),
        tokens=tokens,
        lexicon_size=lexicon.size,
    )


def transcribe_audio(db: Session, language_id: UUID, audio: bytes) -> TranscriptionResult:
    """Raises `phoneme_recognizer.RecognizerUnavailableError` if ASR isn't installed."""
    ipa = phoneme_recognizer.recognize(audio)
    return transcribe_ipa(db, language_id, ipa)
