"""
Pydantic schemas for API request/response validation.
"""

# User schemas
from app.schemas.user import (
    UserBase,
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
    Token,
    TokenData,
)

# Language schemas
from app.schemas.language import (
    LanguageBase,
    LanguageCreate,
    LanguageUpdate,
    LanguageInDB,
    Language,
    LanguageListItem,
)

# Audio schemas
from app.schemas.audio import (
    AudioBase,
    AudioCreate,
    AudioUpdate,
    AudioInDB,
    Audio,
    AudioListItem,
)

# Document schemas
from app.schemas.document import (
    DocumentBase,
    DocumentCreate,
    DocumentUpdate,
    DocumentInDB,
    Document,
    DocumentListItem,
    DocumentFilter,
    DocumentStatistics,
)

# Lexeme / WordForm schemas (Location, Tag, Image schemas also live in this module)
from app.schemas.word import (
    # Lexeme
    Lexeme,
    LexemeCreate,
    LexemeUpdate,
    LexemeListItem,
    LexemeWithForms,
    LexemeFilter,
    LexemeStatistics,
    # WordForm
    WordForm,
    WordFormCreate,
    WordFormUpdate,
    # Relationships
    SynonymCreate,
    AntonymCreate,
    RelatedLexemeCreate,
    TranslationCreate,
    TranslationUpdate,
    SynonymLink,
    AntonymLink,
    TranslationLink,
    LexemeReference,
    # Rhyme
    RhymeMatch,
    # Location
    LocationBase,
    LocationCreate,
    LocationUpdate,
    LocationInDB,
    Location,
    # Tag
    TagBase,
    TagCreate,
    TagUpdate,
    TagInDB,
    Tag,
    # Image
    ImageBase,
    ImageCreate,
    ImageUpdate,
    ImageInDB,
    Image,
    # Aliases for back-compat readers
    Word,
    WordCreate,
    WordUpdate,
    WordListItem,
    WordFilter,
    WordStatistics,
)

__all__ = [
    # User schemas
    "UserBase",
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "UserUpdate",
    "Token",
    "TokenData",
    
    # Language schemas
    "LanguageBase",
    "LanguageCreate",
    "LanguageUpdate",
    "LanguageInDB",
    "Language",
    "LanguageListItem",
    
    # Audio schemas
    "AudioBase",
    "AudioCreate",
    "AudioUpdate",
    "AudioInDB",
    "Audio",
    "AudioListItem",
    
    # Document schemas
    "DocumentBase",
    "DocumentCreate",
    "DocumentUpdate",
    "DocumentInDB",
    "Document",
    "DocumentListItem",
    "DocumentFilter",
    "DocumentStatistics",
    
    # Lexeme / WordForm
    "Lexeme",
    "LexemeCreate",
    "LexemeUpdate",
    "LexemeListItem",
    "LexemeWithForms",
    "LexemeFilter",
    "LexemeStatistics",
    "WordForm",
    "WordFormCreate",
    "WordFormUpdate",
    # Relationships
    "SynonymCreate",
    "AntonymCreate",
    "RelatedLexemeCreate",
    "TranslationCreate",
    "TranslationUpdate",
    "SynonymLink",
    "AntonymLink",
    "TranslationLink",
    "LexemeReference",
    "RhymeMatch",
    # Location
    "LocationBase",
    "LocationCreate",
    "LocationUpdate",
    "LocationInDB",
    "Location",
    # Tag
    "TagBase",
    "TagCreate",
    "TagUpdate",
    "TagInDB",
    "Tag",
    # Image
    "ImageBase",
    "ImageCreate",
    "ImageUpdate",
    "ImageInDB",
    "Image",
    # Back-compat
    "Word",
    "WordCreate",
    "WordUpdate",
    "WordListItem",
    "WordFilter",
    "WordStatistics",
]
