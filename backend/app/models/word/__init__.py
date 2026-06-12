"""
Lexicographic models — Lexemes (concept-level dictionary entries) and
WordForms (surface forms with inflection, IPA, rhyme keys, audio, attestations).
"""
from app.models.word.enums import (
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
    WordStatus,  # alias for LexemeStatus, kept for downstream readability
)

from app.models.word.associations import (
    WordTextType,
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

from app.models.word.lexeme import Lexeme
from app.models.word.word_form import WordForm

__all__ = [
    "Lexeme",
    "WordForm",
    # Enums
    "Animacy",
    "AntonymType",
    "GrammaticalCase",
    "GrammaticalGender",
    "LexemeStatus",
    "PartOfSpeech",
    "Plurality",
    "Register",
    "SynonymNuance",
    "VerbAspect",
    "WordStatus",
    "WordTextType",
    # Associations
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
