"""
Database models for the Nativo language-preservation platform.

All models use UUID primary keys.
"""

from app.models.ai_suggestion import AiSuggestion
from app.models.api_token import ApiToken
from app.models.audio import Audio
from app.models.change_proposal import (
    ChangeProposal,
    ProposalStatus,
    ProposalType,
    ProposalVote,
    VoteChoice,
)
from app.models.document import Document
from app.models.image import Image
from app.models.language import Language
from app.models.learning import DifficultyRating, UserLexemeKnowledge, UserTextProgress
from app.models.location import Location
from app.models.source_snippet import SourceSnippet
from app.models.tag import Tag
from app.models.text import DocumentType, Text
from app.models.text_word_link import TextWordLink, TextWordLinkStatus
from app.models.user import User, UserRole
from app.models.user_language import ProficiencyLevel, UserLanguage
from app.models.word import (
    # Enums
    Animacy,
    AntonymType,
    GrammaticalCase,
    GrammaticalGender,
    Lexeme,
    LexemeStatus,
    PartOfSpeech,
    Plurality,
    Register,
    SpellingVariant,
    SynonymNuance,
    VerbAspect,
    WordForm,
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
    "AiSuggestion",
    "SourceSnippet",
    # Core models
    "User",
    "ApiToken",
    "Language",
    "UserLanguage",
    "Audio",
    "Document",
    "Text",
    "TextWordLink",
    "Location",
    "Tag",
    "ChangeProposal",
    "ProposalVote",
    "ProposalStatus",
    "ProposalType",
    "VoteChoice",
    "Lexeme",
    "WordForm",
    "SpellingVariant",
    "Image",
    "UserLexemeKnowledge",
    "UserTextProgress",
    "DifficultyRating",
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
