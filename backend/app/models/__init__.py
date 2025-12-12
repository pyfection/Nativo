"""
Database models for Nativo language preservation platform.

All models use UUID primary keys for better distributed system compatibility.
"""

from app.models.user import User, UserRole
from app.models.language import Language
from app.models.user_language import UserLanguage, ProficiencyLevel
from app.models.audio import Audio
from app.models.document import Document
from app.models.text import Text, DocumentType
from app.models.text_word_link import TextWordLink, TextWordLinkStatus
from app.models.location import Location
from app.models.image import Image
from app.models.tag import Tag, word_tags
from app.models.password_reset_token import PasswordResetToken
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
    WordTextType,
    word_audio,
    word_image,
    word_texts,
    word_definitions,
    word_synonyms,
    word_antonyms,
    word_related,
    word_translations,
)

__all__ = [
    # Core Models
    "User",
    "Language",
    "UserLanguage",
    "Audio",
    "Document",
    "Text",
    "TextWordLink",
    "Location",
    "Tag",
    "Word",
    "Image",
    "PasswordResetToken",
    
    # User Enums
    "UserRole",
    "ProficiencyLevel",
    
    # Document/Text Enum
    "DocumentType",
    "TextWordLinkStatus",
    
    # Word Enums
    "PartOfSpeech",
    "GrammaticalGender",
    "Plurality",
    "GrammaticalCase",
    "VerbAspect",
    "Animacy",
    "Register",
    "WordStatus",
    "WordTextType",
    
    # Association tables
    "word_tags",
    "word_audio",
    "word_image",
    "word_texts",
    "word_definitions",
    "word_synonyms",
    "word_antonyms",
    "word_related",
    "word_translations",
]
