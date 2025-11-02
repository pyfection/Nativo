"""
Database models for Nativo language preservation platform.

All models use UUID primary keys for better distributed system compatibility.
"""

from app.models.user import User, UserRole
from app.models.language import Language
from app.models.user_language import UserLanguage, ProficiencyLevel
from app.models.audio import Audio
from app.models.document import Document, DocumentType
from app.models.location import Location
from app.models.image import Image
from app.models.tag import Tag, word_tags
from app.models.word import (
    Word,
    PartOfSpeech,
    GrammaticalGender,
    Plurality,
    GrammaticalCase,
    VerbAspect,
    Animacy,
    Register,
    WordStatus,
    WordDocumentType,
    word_audio,
    word_image,
    word_documents,
    word_synonyms,
    word_antonyms,
    word_related,
)

__all__ = [
    # Core Models
    "User",
    "Language",
    "UserLanguage",
    "Audio",
    "Document",
    "Location",
    "Tag",
    "Word",
    "Image",
    
    # User Enums
    "UserRole",
    "ProficiencyLevel",
    
    # Document Enum
    "DocumentType",
    
    # Word Enums
    "PartOfSpeech",
    "GrammaticalGender",
    "Plurality",
    "GrammaticalCase",
    "VerbAspect",
    "Animacy",
    "Register",
    "WordStatus",
    "WordDocumentType",
    
    # Association tables
    "word_tags",
    "word_audio",
    "word_image",
    "word_documents",
    "word_synonyms",
    "word_antonyms",
    "word_related",
]
