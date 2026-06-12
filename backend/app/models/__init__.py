"""
Database models for the Nativo language-preservation platform.

All models use UUID primary keys.
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
from app.models.tag import Tag
from app.models.word import (
    Lexeme,
    WordForm,
    # Enums
    Animacy,
    AntonymType,
    GrammaticalCase,
    GrammaticalGender,
    LexemeStatus,
    PartOfSpeech,
    Plurality,
    Register,
    SynonymNuance,
    VerbAspect,
    WordStatus,
    WordTextType,
    # Associations
    lexeme_antonyms,
    lexeme_definitions,
    lexeme_images,
    lexeme_related,
    lexeme_synonyms,
    lexeme_tags,
    lexeme_texts,
    lexeme_translations,
    word_form_audio,
    word_form_locations,
)

__all__ = [
    # Core models
    "User",
    "Language",
    "UserLanguage",
    "Audio",
    "Document",
    "Text",
    "TextWordLink",
    "Location",
    "Tag",
    "Lexeme",
    "WordForm",
    "Image",
    # User enums
    "UserRole",
    "ProficiencyLevel",
    # Document/Text enums
    "DocumentType",
    "TextWordLinkStatus",
    # Lexeme enums
    "PartOfSpeech",
    "GrammaticalGender",
    "Plurality",
    "GrammaticalCase",
    "VerbAspect",
    "Animacy",
    "Register",
    "LexemeStatus",
    "WordStatus",
    "WordTextType",
    "SynonymNuance",
    "AntonymType",
    # Association tables
    "lexeme_antonyms",
    "lexeme_definitions",
    "lexeme_images",
    "lexeme_related",
    "lexeme_synonyms",
    "lexeme_tags",
    "lexeme_texts",
    "lexeme_translations",
    "word_form_audio",
    "word_form_locations",
]
