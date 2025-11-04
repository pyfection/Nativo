"""
Association tables for Word model many-to-many relationships.
"""
from sqlalchemy import Table, Column, String, DateTime, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import enum

from app.database import Base


class WordDocumentType(str, enum.Enum):
    """Types of word-document relationships"""
    DEFINITION = "definition"
    LITERAL_TRANSLATION = "literal_translation"
    CONTEXT_NOTE = "context_note"
    USAGE_EXAMPLE = "usage_example"
    ETYMOLOGY = "etymology"
    CULTURAL_SIGNIFICANCE = "cultural_significance"
    OTHER = "other"


# Association table for Word-Audio many-to-many relationship
word_audio = Table(
    'word_audio',
    Base.metadata,
    Column('word_id', UUID(as_uuid=True), ForeignKey('words.id'), primary_key=True),
    Column('audio_id', UUID(as_uuid=True), ForeignKey('audio.id'), primary_key=True),
    Column('is_primary', Boolean, default=False),  # Mark one as primary pronunciation
    Column('created_at', DateTime, default=datetime.utcnow, nullable=False)
)


# Association table for Word-Image many-to-many relationship
word_image = Table(
    'word_image',
    Base.metadata,
    Column('word_id', UUID(as_uuid=True), ForeignKey('words.id'), primary_key=True),
    Column('image_id', UUID(as_uuid=True), ForeignKey('images.id'), primary_key=True),
    Column('is_primary', Boolean, default=False),  # Mark one as primary image
    Column('created_at', DateTime, default=datetime.utcnow, nullable=False)
)


# Association table for Word-Document many-to-many relationship
# Links words to documents with a relationship type
word_documents = Table(
    'word_documents',
    Base.metadata,
    Column('word_id', UUID(as_uuid=True), ForeignKey('words.id'), primary_key=True),
    Column('document_id', UUID(as_uuid=True), ForeignKey('documents.id'), primary_key=True),
    Column('relationship_type', SQLEnum(WordDocumentType), nullable=False, primary_key=True),
    Column('created_at', DateTime, default=datetime.utcnow, nullable=False)
)


# Association table for synonyms (Word-to-Word self-referential)
word_synonyms = Table(
    'word_synonyms',
    Base.metadata,
    Column('word_id', UUID(as_uuid=True), ForeignKey('words.id'), primary_key=True),
    Column('synonym_id', UUID(as_uuid=True), ForeignKey('words.id'), primary_key=True),
    Column('created_at', DateTime, default=datetime.utcnow, nullable=False)
)


# Association table for antonyms (Word-to-Word self-referential)
word_antonyms = Table(
    'word_antonyms',
    Base.metadata,
    Column('word_id', UUID(as_uuid=True), ForeignKey('words.id'), primary_key=True),
    Column('antonym_id', UUID(as_uuid=True), ForeignKey('words.id'), primary_key=True),
    Column('created_at', DateTime, default=datetime.utcnow, nullable=False)
)


# Association table for related words (Word-to-Word self-referential)
word_related = Table(
    'word_related',
    Base.metadata,
    Column('word_id', UUID(as_uuid=True), ForeignKey('words.id'), primary_key=True),
    Column('related_word_id', UUID(as_uuid=True), ForeignKey('words.id'), primary_key=True),
    Column('relationship_type', String(100), nullable=True),  # e.g., 'derived_from', 'compound_part'
    Column('created_at', DateTime, default=datetime.utcnow, nullable=False)
)


# Association table for word translations (Word-to-Word self-referential for cross-language translations)
word_translations = Table(
    'word_translations',
    Base.metadata,
    Column('word_id', UUID(as_uuid=True), ForeignKey('words.id'), primary_key=True),
    Column('translation_id', UUID(as_uuid=True), ForeignKey('words.id'), primary_key=True),
    Column('notes', String(500), nullable=True),  # Additional context about the translation
    Column('created_at', DateTime, default=datetime.utcnow, nullable=False),
    Column('created_by_id', UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
)

