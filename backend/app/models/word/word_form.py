"""
WordForm — one surface form of a Lexeme.

A WordForm holds the actual string, IPA, rhyme keys, inflectional features
(case, plurality, verb aspect), audio recordings, and the locations where
this specific pronunciation/form was attested. Exactly one WordForm per
Lexeme should have `is_lemma=True` (the canonical citation form).
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.word.associations import word_form_audio, word_form_locations
from app.models.word.enums import GrammaticalCase, Plurality, VerbAspect


def _now() -> datetime:
    return datetime.now(UTC)


class WordForm(Base):
    __tablename__ = "word_forms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lexeme_id = Column(
        UUID(as_uuid=True), ForeignKey("lexemes.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Surface representation
    form = Column(String(255), nullable=False, index=True)
    romanization = Column(String(255), nullable=True, index=True)
    ipa_pronunciation = Column(String(255), nullable=True)

    # Computed from IPA — see app.utils.rhyme. Recompute on IPA change.
    rhyme_key = Column(String(255), nullable=True, index=True)
    near_rhyme_key = Column(String(255), nullable=True, index=True)

    # Canonical citation form for the parent Lexeme. Lexeme.lemma mirrors
    # this WordForm's `form` for cheap search.
    is_lemma = Column(Boolean, default=False, nullable=False, index=True)

    # Inflectional features. These enums were created by the initial schema
    # with UPPERCASE Postgres labels; default SQLAlchemy storage (.name) is
    # what Postgres expects here. Do NOT add values_callable.
    plurality = Column(SQLEnum(Plurality, name="plurality"), nullable=True)
    grammatical_case = Column(SQLEnum(GrammaticalCase, name="grammaticalcase"), nullable=True)
    verb_aspect = Column(SQLEnum(VerbAspect, name="verbaspect"), nullable=True)

    notes = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=_now, nullable=False)
    updated_at = Column(DateTime, default=_now, onupdate=_now, nullable=False)

    # Relationships
    lexeme = relationship("Lexeme", back_populates="forms")
    audio_files = relationship("Audio", secondary=word_form_audio, backref="word_forms")
    confirmed_at = relationship("Location", secondary=word_form_locations, backref="word_forms")
    text_links = relationship(
        "TextWordLink",
        back_populates="word_form",
        cascade="all, delete-orphan",
    )
    spelling_variants = relationship(
        "SpellingVariant",
        back_populates="word_form",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<WordForm(id={self.id}, form='{self.form}', lexeme_id={self.lexeme_id}, "
            f"is_lemma={self.is_lemma})>"
        )
