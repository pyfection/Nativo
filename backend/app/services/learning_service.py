"""
Guided learning path: implicit vocabulary scoring + text sequencing.

The sequencer is a read-time projection over existing data (confirmed
TextWordLinks), in the same spirit as the regional-rendering and spelling
layers: nothing about difficulty is stored per text, it is computed per
learner from which lexemes they know.

Scoring rules (agreed design):
- Tapping a word to look it up while reading is a "don't know" signal:
  first contact -> score 0, later taps -> -1.
- Finishing a text without tapping a word is a "know" signal for every
  confirmed-linked lexeme in it: first contact -> score 4, later -> +1.
- Clicks apply immediately; the no-tap bonus applies only at completion,
  so an abandoned (skimmed) text marks nothing as known.
"""

import re
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.learning import (
    KNOWN_SCORE_THRESHOLD,
    SCORE_MAX,
    SCORE_MIN,
    DifficultyRating,
    UserLexemeKnowledge,
    UserTextProgress,
)
from app.models.text import Text, TextStatus
from app.models.text_word_link import TextWordLink, TextWordLinkStatus
from app.models.word import Lexeme, WordForm

# A text only qualifies for the learning path when at least this fraction of
# its word-ish tokens are covered by confirmed links — half-linked texts have
# unknowable difficulty.
LINK_COVERAGE_THRESHOLD = 0.9

# New-word budget per step, keyed by the reader's difficulty verdict on their
# most recently completed text in the language. Static tiers, deliberately
# simple; tune here.
DEFAULT_NEW_WORD_BUDGET = 8
BUDGET_BY_RATING = {
    DifficultyRating.EASY: 12,
    DifficultyRating.JUST_RIGHT: 8,
    DifficultyRating.CHALLENGING: 4,
    DifficultyRating.TOO_HARD: 0,
}

# \w covers letters/digits/underscore across Unicode in Python 3 — good
# enough to count "word-ish" tokens for coverage purposes.
_TOKEN_RE = re.compile(r"\w+", re.UNICODE)


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


def record_click(db: Session, user_id: UUID, lexeme_id: UUID) -> UserLexemeKnowledge:
    """A reader tapped a word to look it up — lower its score."""
    row = db.get(UserLexemeKnowledge, (user_id, lexeme_id))
    if row is None:
        row = UserLexemeKnowledge(user_id=user_id, lexeme_id=lexeme_id, score=SCORE_MIN)
        db.add(row)
    else:
        row.score = max(SCORE_MIN, row.score - 1)
    db.flush()
    return row


def _confirmed_lexeme_ids_for_text(db: Session, text_id: UUID) -> set[UUID]:
    rows = (
        db.query(WordForm.lexeme_id)
        .join(TextWordLink, TextWordLink.word_form_id == WordForm.id)
        .filter(
            TextWordLink.text_id == text_id,
            TextWordLink.status == TextWordLinkStatus.CONFIRMED,
        )
        .distinct()
        .all()
    )
    return {r[0] for r in rows}


def complete_text(
    db: Session,
    user_id: UUID,
    text: Text,
    rating: DifficultyRating,
    clicked_lexeme_ids: set[UUID] | None = None,
) -> UserTextProgress:
    """
    Record a finished reading and apply the no-tap "know" bonus.

    `clicked_lexeme_ids` is the client's record of what was tapped during
    this reading session; those lexemes were already scored down by
    record_click, so they are excluded from the bonus. Re-completing a text
    updates the rating and re-applies the bonus (idempotent per lexeme in
    effect: +1 capped, or another confirmation of an already-known word).
    """
    clicked = clicked_lexeme_ids or set()

    progress = db.get(UserTextProgress, (user_id, text.id))
    if progress is None:
        progress = UserTextProgress(
            user_id=user_id, text_id=text.id, difficulty_rating=rating
        )
        db.add(progress)
    else:
        progress.difficulty_rating = rating

    for lexeme_id in _confirmed_lexeme_ids_for_text(db, text.id) - clicked:
        row = db.get(UserLexemeKnowledge, (user_id, lexeme_id))
        if row is None:
            db.add(
                UserLexemeKnowledge(user_id=user_id, lexeme_id=lexeme_id, score=SCORE_MAX)
            )
        else:
            row.score = min(SCORE_MAX, row.score + 1)

    db.flush()
    return progress


def known_lexeme_ids(db: Session, user_id: UUID, language_id: UUID) -> set[UUID]:
    rows = (
        db.query(UserLexemeKnowledge.lexeme_id)
        .join(Lexeme, Lexeme.id == UserLexemeKnowledge.lexeme_id)
        .filter(
            UserLexemeKnowledge.user_id == user_id,
            UserLexemeKnowledge.score >= KNOWN_SCORE_THRESHOLD,
            Lexeme.language_id == language_id,
        )
        .all()
    )
    return {r[0] for r in rows}


# ---------------------------------------------------------------------------
# Sequencing
# ---------------------------------------------------------------------------


def _current_budget(db: Session, user_id: UUID, language_id: UUID) -> int:
    latest = (
        db.query(UserTextProgress)
        .join(Text, Text.id == UserTextProgress.text_id)
        .filter(
            UserTextProgress.user_id == user_id,
            Text.language_id == language_id,
        )
        .order_by(UserTextProgress.completed_at.desc())
        .first()
    )
    if latest is None:
        return DEFAULT_NEW_WORD_BUDGET
    return BUDGET_BY_RATING[latest.difficulty_rating]


def _link_coverage(text: Text, links: list[TextWordLink]) -> float:
    """Fraction of word-ish tokens covered by confirmed link spans."""
    tokens = list(_TOKEN_RE.finditer(text.content or ""))
    if not tokens:
        return 0.0
    spans = [
        (link.start_char, link.end_char)
        for link in links
        if link.status == TextWordLinkStatus.CONFIRMED
    ]
    covered = 0
    for tok in tokens:
        if any(start <= tok.start() and tok.end() <= end for start, end in spans):
            covered += 1
    return covered / len(tokens)


def _corpus_frequency(db: Session, language_id: UUID) -> dict[UUID, int]:
    """Confirmed-link count per lexeme across all texts in the language."""
    rows = (
        db.query(WordForm.lexeme_id, func.count(TextWordLink.id))
        .join(TextWordLink, TextWordLink.word_form_id == WordForm.id)
        .join(Text, Text.id == TextWordLink.text_id)
        .filter(
            Text.language_id == language_id,
            TextWordLink.status == TextWordLinkStatus.CONFIRMED,
        )
        .group_by(WordForm.lexeme_id)
        .all()
    )
    return {lexeme_id: count for lexeme_id, count in rows}


def get_learning_path(
    db: Session,
    language_id: UUID,
    user_id: UUID | None = None,
    limit: int = 20,
) -> list[dict]:
    """
    The learner's line through the corpus.

    Returns dicts (schema-shaped by the endpoint) ordered: completed texts
    first (chronologically), then eligible unread texts easiest-first under
    the current new-word budget. Anonymous callers get the cold-start
    ordering (fewest unique lexemes, most frequent vocabulary first).
    """
    texts = (
        db.query(Text)
        .filter(
            Text.language_id == language_id,
            Text.status == TextStatus.PUBLISHED,
        )
        .order_by(Text.created_at.asc())
        .all()
    )
    if not texts:
        return []

    links_by_text: dict[UUID, list[TextWordLink]] = {}
    for text in texts:
        links_by_text[text.id] = (
            db.query(TextWordLink).filter(TextWordLink.text_id == text.id).all()
        )

    known: set[UUID] = set()
    completed: dict[UUID, UserTextProgress] = {}
    budget = DEFAULT_NEW_WORD_BUDGET
    if user_id is not None:
        known = known_lexeme_ids(db, user_id, language_id)
        completed = {
            p.text_id: p
            for p in db.query(UserTextProgress)
            .join(Text, Text.id == UserTextProgress.text_id)
            .filter(
                UserTextProgress.user_id == user_id,
                Text.language_id == language_id,
            )
            .all()
        }
        budget = _current_budget(db, user_id, language_id)

    frequency = _corpus_frequency(db, language_id)

    entries = []
    for text in texts:
        links = links_by_text[text.id]
        coverage = _link_coverage(text, links)
        if coverage < LINK_COVERAGE_THRESHOLD and text.id not in completed:
            continue  # difficulty unknowable; editors need to finish linking

        lexemes = _confirmed_lexeme_ids_for_text(db, text.id)
        new_lexemes = lexemes - known
        total = len(lexemes)
        known_pct = 100.0 if total == 0 else round(100 * (total - len(new_lexemes)) / total, 1)

        entries.append(
            {
                "text_id": text.id,
                "document_id": text.document_id,
                "title": text.title,
                "total_lexemes": total,
                "new_lexeme_count": len(new_lexemes),
                "known_pct": known_pct,
                "completed_at": completed[text.id].completed_at
                if text.id in completed
                else None,
                "difficulty_rating": completed[text.id].difficulty_rating
                if text.id in completed
                else None,
                # sort keys, stripped before returning
                "_freq": (
                    sum(frequency.get(lx, 0) for lx in lexemes) / total if total else 0
                ),
                "_pin": text.learning_order,
            }
        )

    done = [e for e in entries if e["completed_at"] is not None]
    done.sort(key=lambda e: e["completed_at"])

    unread = [e for e in entries if e["completed_at"] is None]
    # Easiest-first: fewest new words, then highest average corpus frequency
    # (which is also the cold-start order when nothing is known yet).
    unread.sort(key=lambda e: (e["new_lexeme_count"], -e["_freq"]))

    # Editor-pinned texts jump the computed queue (and the budget) — the pin
    # is the curated on-ramp, so curation wins over the algorithm.
    pinned = sorted(
        (e for e in unread if e["_pin"] is not None), key=lambda e: e["_pin"]
    )
    rest = [e for e in unread if e["_pin"] is None]

    within = [e for e in rest if e["new_lexeme_count"] <= budget]
    beyond = [e for e in rest if e["new_lexeme_count"] > budget]

    # A "too hard" verdict asks for a zero-new consolidation text; if the
    # corpus has none, recommend the gentlest available rather than nothing.
    ordered_unread = pinned + within + beyond
    recommended = ordered_unread[0] if ordered_unread else None

    path = done + ordered_unread
    for entry in path:
        entry.pop("_freq")
        entry.pop("_pin")
        if entry["completed_at"] is not None:
            entry["state"] = "completed"
        elif entry is recommended:
            entry["state"] = "recommended"
        else:
            entry["state"] = "upcoming"

    return path[: limit + len(done)]
