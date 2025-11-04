"""
Word package - models, enums, and associations for word management.
"""

from app.models.word.enums import (
    PartOfSpeech,
    GrammaticalGender,
    Plurality,
    GrammaticalCase,
    VerbAspect,
    Animacy,
    Register,
    WordStatus,
)

from app.models.word.word import Word

from app.models.word.associations import (
    word_audio,
    word_image,
    word_texts,
    word_definitions,
    word_synonyms,
    word_antonyms,
    word_related,
    WordTextType,
)

__all__ = [
    # Models
    "Word",
    
    # Enums
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
    "word_audio",
    "word_image",
    "word_texts",
    "word_definitions",
    "word_synonyms",
    "word_antonyms",
    "word_related",
]

