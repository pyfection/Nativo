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

# Word schemas (includes Location, Tag, Image schemas too)
from app.schemas.word import (
    # Word schemas
    WordBase,
    WordCreate,
    WordUpdate,
    WordInDB,
    Word,
    WordListItem,
    WordWithRelations,
    WordFilter,
    WordStatistics,
    
    # Location schemas
    LocationBase,
    LocationCreate,
    LocationUpdate,
    LocationInDB,
    Location,
    
    # Tag schemas
    TagBase,
    TagCreate,
    TagUpdate,
    TagInDB,
    Tag,
    
    # Image schemas
    ImageBase,
    ImageCreate,
    ImageUpdate,
    ImageInDB,
    Image,
    
    # Relationship schemas
    WordRelationshipCreate,
    WordTextAssociation,
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
    
    # Word schemas
    "WordBase",
    "WordCreate",
    "WordUpdate",
    "WordInDB",
    "Word",
    "WordListItem",
    "WordWithRelations",
    "WordFilter",
    "WordStatistics",
    
    # Location schemas
    "LocationBase",
    "LocationCreate",
    "LocationUpdate",
    "LocationInDB",
    "Location",
    
    # Tag schemas
    "TagBase",
    "TagCreate",
    "TagUpdate",
    "TagInDB",
    "Tag",
    
    # Image schemas
    "ImageBase",
    "ImageCreate",
    "ImageUpdate",
    "ImageInDB",
    "Image",
    
    # Relationship schemas
    "WordRelationshipCreate",
    "WordTextAssociation",
]
