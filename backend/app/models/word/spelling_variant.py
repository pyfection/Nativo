"""
SpellingVariant — a non-standard way of writing a WordForm.

Many endangered languages have no settled orthography, so the same form is
written several ways even when it's pronounced identically. A SpellingVariant
records one such alternative spelling and maps it back to the WordForm whose
`form` is the standard. This drives two things:

- Looking up "how do I write this properly?" — resolve a variant to its
  standard form.
- Suggesting corrections across a document written in a non-standard hand.

A variant is purely orthographic: it shares the parent WordForm's pronunciation,
inflection, meaning and attestations. If the pronunciation actually differs by
region, that's a separate WordForm with its own attested locations, not a
SpellingVariant.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, validates

from app.database import Base
from app.utils.text_normalize import fold_for_match


def _now() -> datetime:
    return datetime.now(UTC)


class SpellingVariant(Base):
    __tablename__ = "spelling_variants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    word_form_id = Column(
        UUID(as_uuid=True),
        ForeignKey("word_forms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # The alternative spelling as written, e.g. "eich".
    variant = Column(String(255), nullable=False, index=True)
    # Case/diacritic-folded match key (app.utils.text_normalize.fold_for_match).
    # Indexed so resolving a token is a single equality lookup, like rhyme_key.
    normalized = Column(String(255), nullable=False, index=True)

    # Free-text provenance, e.g. "pre-standard", "common in older texts".
    note = Column(String(500), nullable=True)

    created_by_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    created_at = Column(DateTime, default=_now, nullable=False)
    updated_at = Column(DateTime, default=_now, onupdate=_now, nullable=False)

    word_form = relationship("WordForm", back_populates="spelling_variants")
    created_by = relationship("User", foreign_keys=[created_by_id])

    __table_args__ = (
        UniqueConstraint("word_form_id", "variant", name="uq_spelling_variants_form_variant"),
    )

    @validates("variant")
    def _sync_normalized(self, _key: str, value: str) -> str:
        """Keep the match key in lockstep with the spelling on every write path
        (service, admin, raw ORM), so resolution never misses a variant."""
        self.normalized = fold_for_match(value or "")
        return value

    def __repr__(self) -> str:
        return (
            f"<SpellingVariant(id={self.id}, variant='{self.variant}', "
            f"word_form_id={self.word_form_id})>"
        )
