"""
Per-user language-learning state.

Two small tables power the guided learning path:

- `UserLexemeKnowledge` — how well a user knows each lexeme, as a 0-4 score
  maintained implicitly from reading behaviour (tapping a word to look it up
  lowers the score, finishing a text without tapping it raises it). V1 reads
  the score as binary: known means score >= KNOWN_SCORE_THRESHOLD.
- `UserTextProgress` — which texts a user finished, and how difficult they
  said it was. The most recent rating per language drives the new-word
  budget of the sequencer.
"""

import enum
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


def _now() -> datetime:
    return datetime.now(UTC)

# Score bounds and the v1 binary interpretation. The 0-4 scale is stored (not
# a boolean) so a later review/SRS layer can distinguish shaky words from
# solid ones without a migration.
SCORE_MIN = 0
SCORE_MAX = 4
KNOWN_SCORE_THRESHOLD = 3


class DifficultyRating(str, enum.Enum):
    """How difficult the reader found a text, asked on completion."""

    EASY = "easy"
    JUST_RIGHT = "just_right"
    CHALLENGING = "challenging"
    TOO_HARD = "too_hard"


class UserLexemeKnowledge(Base):
    """
    A user's familiarity with one lexeme (0-4).

    Score transitions (applied by learning_service):
    - tap to look up, first contact  -> SCORE_MIN
    - tap to look up, later          -> -1 (floor SCORE_MIN)
    - text completed without tapping, first contact -> SCORE_MAX
    - text completed without tapping, later         -> +1 (cap SCORE_MAX)
    """

    __tablename__ = "user_lexeme_knowledge"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    lexeme_id = Column(
        UUID(as_uuid=True),
        ForeignKey("lexemes.id", ondelete="CASCADE"),
        primary_key=True,
    )

    score = Column(Integer, nullable=False, default=SCORE_MIN)

    first_seen_at = Column(DateTime, default=_now, nullable=False)
    updated_at = Column(DateTime, default=_now, onupdate=_now, nullable=False)

    user = relationship("User")
    lexeme = relationship("Lexeme")

    def __repr__(self):
        return (
            f"<UserLexemeKnowledge(user_id={self.user_id}, "
            f"lexeme_id={self.lexeme_id}, score={self.score})>"
        )


class UserTextProgress(Base):
    """A completed reading of a text, with the reader's difficulty verdict."""

    __tablename__ = "user_text_progress"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    text_id = Column(
        UUID(as_uuid=True),
        ForeignKey("texts.id", ondelete="CASCADE"),
        primary_key=True,
    )

    difficulty_rating = Column(
        # Lowercase Postgres labels, matching the textwordlinkstatus convention.
        SQLEnum(
            DifficultyRating,
            name="difficultyrating",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
    )

    completed_at = Column(DateTime, default=_now, nullable=False)

    user = relationship("User")
    text = relationship("Text")

    def __repr__(self):
        return (
            f"<UserTextProgress(user_id={self.user_id}, text_id={self.text_id}, "
            f"rating={self.difficulty_rating})>"
        )
