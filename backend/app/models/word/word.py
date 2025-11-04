"""
Word model for endangered language preservation.
"""
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Boolean, Enum as SQLEnum, and_
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base
from app.models.word.enums import (
    PartOfSpeech,
    GrammaticalGender,
    Plurality,
    GrammaticalCase,
    VerbAspect,
    Animacy,
    Register,
    WordStatus
)
from app.models.word.associations import (
    word_audio,
    word_image,
    word_documents,
    word_synonyms,
    word_antonyms,
    word_related,
    word_translations,
    WordDocumentType
)



class Word(Base):
    """
    Core word model for endangered language preservation.
    
    Words can be linked to Document records which can contain:
    - Definitions
    - Etymology
    - Cultural significance
    - Usage examples
    - And more
    
    Documents can be full texts (stories) or small snippets (a single definition).
    Each word in a document's content can be linked back to its Word record.
    """
    __tablename__ = "words"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Core Word Information
    word = Column(String(255), nullable=False, index=True)
    language_id = Column(UUID(as_uuid=True), ForeignKey("languages.id"), nullable=False, index=True)
    romanization = Column(String(255), nullable=True, index=True)  # For non-Latin scripts
    ipa_pronunciation = Column(String(255), nullable=True)  # International Phonetic Alphabet

    # Linguistic Information
    part_of_speech = Column(SQLEnum(PartOfSpeech), nullable=True, index=True)
    gender = Column(SQLEnum(GrammaticalGender), nullable=True)
    plurality = Column(SQLEnum(Plurality), nullable=True)
    grammatical_case = Column(SQLEnum(GrammaticalCase), nullable=True)
    verb_aspect = Column(SQLEnum(VerbAspect), nullable=True)
    animacy = Column(SQLEnum(Animacy), nullable=True)
    
    # Cultural Context
    language_register = Column(SQLEnum(Register), nullable=True, default=Register.NEUTRAL)
    
    # Location where this word/pronunciation was confirmed
    confirmed_at_id = Column(UUID(as_uuid=True), ForeignKey("locations.id"), nullable=True)
    
    # Metadata
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    verified_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    is_verified = Column(Boolean, default=False, index=True)
    status = Column(SQLEnum(WordStatus), default=WordStatus.DRAFT, index=True)
    source = Column(String(500), nullable=True)  # Source of documentation
    notes = Column(Text, nullable=True)  # Additional notes for internal use
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    language = relationship("Language", back_populates="words")
    created_by = relationship("User", foreign_keys=[created_by_id], back_populates="words_created")
    verified_by = relationship("User", foreign_keys=[verified_by_id], back_populates="words_verified")
    confirmed_at = relationship("Location")
    
    # Many-to-many relationships
    audio_files = relationship("Audio", secondary=word_audio, backref="words")
    images = relationship("Image", secondary=word_image, backref="words")
    tags = relationship("Tag", secondary="word_tags", back_populates="words")
    
    # Document relationships by type
    definitions = relationship(
        "Document",
        secondary=word_documents,
        primaryjoin=id == word_documents.c.word_id,
        secondaryjoin="and_(Document.id == word_documents.c.document_id, word_documents.c.relationship_type == 'definition')",
        viewonly=True
    )
    
    literal_translations = relationship(
        "Document",
        secondary=word_documents,
        primaryjoin=id == word_documents.c.word_id,
        secondaryjoin="and_(Document.id == word_documents.c.document_id, word_documents.c.relationship_type == 'literal_translation')",
        viewonly=True
    )
    
    context_notes = relationship(
        "Document",
        secondary=word_documents,
        primaryjoin=id == word_documents.c.word_id,
        secondaryjoin="and_(Document.id == word_documents.c.document_id, word_documents.c.relationship_type == 'context_note')",
        viewonly=True
    )
    
    usage_examples = relationship(
        "Document",
        secondary=word_documents,
        primaryjoin=id == word_documents.c.word_id,
        secondaryjoin="and_(Document.id == word_documents.c.document_id, word_documents.c.relationship_type == 'usage_example')",
        viewonly=True
    )
    
    etymologies = relationship(
        "Document",
        secondary=word_documents,
        primaryjoin=id == word_documents.c.word_id,
        secondaryjoin="and_(Document.id == word_documents.c.document_id, word_documents.c.relationship_type == 'etymology')",
        viewonly=True
    )
    
    cultural_significance = relationship(
        "Document",
        secondary=word_documents,
        primaryjoin=id == word_documents.c.word_id,
        secondaryjoin="and_(Document.id == word_documents.c.document_id, word_documents.c.relationship_type == 'cultural_significance')",
        viewonly=True
    )
    
    # Generic relationship for all documents (including stories where word is mentioned)
    documents = relationship("Document", secondary=word_documents, back_populates="linked_words", viewonly=True)
    
    # Self-referential relationships
    synonyms = relationship(
        "Word",
        secondary=word_synonyms,
        primaryjoin=id == word_synonyms.c.word_id,
        secondaryjoin=id == word_synonyms.c.synonym_id,
        backref="synonym_of"
    )
    
    antonyms = relationship(
        "Word",
        secondary=word_antonyms,
        primaryjoin=id == word_antonyms.c.word_id,
        secondaryjoin=id == word_antonyms.c.antonym_id,
        backref="antonym_of"
    )
    
    related_words = relationship(
        "Word",
        secondary=word_related,
        primaryjoin=id == word_related.c.word_id,
        secondaryjoin=id == word_related.c.related_word_id,
        backref="related_to"
    )
    
    # Translations (cross-language word equivalents)
    translations = relationship(
        "Word",
        secondary=word_translations,
        primaryjoin=id == word_translations.c.word_id,
        secondaryjoin=id == word_translations.c.translation_id,
        backref="translated_from"
    )
    
    def __repr__(self):
        return f"<Word(id={self.id}, word='{self.word}', language_id={self.language_id}, status={self.status})>"
    
    class Config:
        """Pydantic configuration"""
        use_enum_values = True
