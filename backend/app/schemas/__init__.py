"""
Pydantic schemas for API request/response validation.
"""

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
    
    # Document schemas
    DocumentBase,
    DocumentCreate,
    DocumentUpdate,
    DocumentInDB,
    Document,
    DocumentListItem,
    DocumentFilter,
    DocumentStatistics,
    
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
    WordDocumentAssociation,
)

__all__ = [
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
    
    # Document schemas
    "DocumentBase",
    "DocumentCreate",
    "DocumentUpdate",
    "DocumentInDB",
    "Document",
    "DocumentListItem",
    "DocumentFilter",
    "DocumentStatistics",
    
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
    "WordDocumentAssociation",
]
