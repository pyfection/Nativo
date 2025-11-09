"""
Document management endpoints.

Documents group together Text records in multiple languages (translations).
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import UUID
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.models.document import Document
from app.models.text import Text
from app.schemas.document import (
    DocumentWithTexts, 
    DocumentListItem,
    DocumentFilter
)
from app.schemas.text import TextCreate, TextUpdate, Text as TextSchema
from app.api.deps import get_current_active_user, require_contributor
from app.services.auth_service import require_resource_owner

router = APIRouter()


@router.get("/", response_model=list[DocumentListItem])
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    language_id: Optional[UUID] = None,
    search_term: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List all documents.
    
    Returns documents with text in the specified language (or primary text).
    Filters by language if language_id is provided.
    """
    query = db.query(Document)
    
    # If language_id specified, only show documents that have text in that language
    if language_id:
        query = query.join(Document.texts).filter(Text.language_id == language_id)
    
    # Get documents
    documents = query.offset(skip).limit(limit).all()
    
    # Build list items with appropriate text for each document
    result = []
    for doc in documents:
        # Find the text to display
        if language_id:
            # Try to get text in requested language
            text = next((t for t in doc.texts if t.language_id == language_id), None)
        else:
            # Get primary text
            text = next((t for t in doc.texts if t.is_primary), None)
        
        # Fallback to any text if none found
        if not text and doc.texts:
            text = doc.texts[0]
        
        if text:
            # Apply search filter if provided
            if search_term:
                search_lower = search_term.lower()
                if search_lower not in text.title.lower() and search_lower not in text.content.lower():
                    continue
            
            result.append(DocumentListItem(
                id=doc.id,
                title=text.title,
                content_preview=text.content[:200] if len(text.content) > 200 else text.content,
                source=text.source,
                language_id=text.language_id,
                created_at=doc.created_at,
                text_count=len(doc.texts)
            ))
    
    return result


@router.get("/{document_id}", response_model=DocumentWithTexts)
async def get_document(
    document_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a document with all its texts (translations).
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return document


@router.get("/{document_id}/language/{language_id}")
async def get_document_for_language(
    document_id: UUID,
    language_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a document's text in a specific language.
    Returns the primary text if the requested language is not available.
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Try to find text in requested language
    text = next((t for t in document.texts if t.language_id == language_id), None)
    
    # Fallback to primary text
    if not text:
        text = next((t for t in document.texts if t.is_primary), None)
    
    # Fallback to any text
    if not text and document.texts:
        text = document.texts[0]
    
    if not text:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No text found for this document"
        )
    
    return {
        "document": document,
        "text": text
    }


@router.post("/", response_model=DocumentWithTexts, status_code=status.HTTP_201_CREATED)
async def create_document(
    text_data: TextCreate,
    current_user: User = Depends(require_contributor),
    db: Session = Depends(get_db)
):
    """
    Create a new document with an initial text.
    
    Requires: NATIVE_SPEAKER, RESEARCHER, or ADMIN role
    """
    # Create document
    new_document = Document(
        created_by_id=current_user.id
    )
    db.add(new_document)
    db.flush()  # Get the document ID
    
    # Create initial text
    new_text = Text(
        **text_data.model_dump(exclude_unset=True),
        document_id=new_document.id,
        created_by_id=current_user.id
    )
    db.add(new_text)
    
    db.commit()
    db.refresh(new_document)
    
    return new_document


@router.post("/{document_id}/texts", response_model=TextSchema, status_code=status.HTTP_201_CREATED)
async def add_translation(
    document_id: UUID,
    text_data: TextCreate,
    current_user: User = Depends(require_contributor),
    db: Session = Depends(get_db)
):
    """
    Add a translation (new text) to an existing document.
    
    Requires: NATIVE_SPEAKER, RESEARCHER, or ADMIN role
    """
    # Check document exists
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Create new text
    new_text = Text(
        **text_data.model_dump(exclude_unset=True),
        document_id=document_id,
        created_by_id=current_user.id
    )
    db.add(new_text)
    db.commit()
    db.refresh(new_text)
    
    return new_text


@router.put("/{document_id}/texts/{text_id}", response_model=TextSchema)
async def update_text(
    document_id: UUID,
    text_id: UUID,
    text_data: TextUpdate,
    current_user: User = Depends(require_contributor),
    db: Session = Depends(get_db)
):
    """
    Update a specific text within a document.
    
    - Users can update their own texts
    - ADMIN can update any text
    """
    text = db.query(Text).filter(
        Text.id == text_id,
        Text.document_id == document_id
    ).first()
    
    if not text:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Text not found"
        )
    
    # Check ownership
    require_resource_owner(current_user, text.created_by_id)
    
    # Update text fields
    for field, value in text_data.model_dump(exclude_unset=True).items():
        setattr(text, field, value)
    
    db.commit()
    db.refresh(text)
    
    return text


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    current_user: User = Depends(require_contributor),
    db: Session = Depends(get_db)
):
    """
    Delete a document and all its texts.
    
    - Users can delete their own documents
    - ADMIN can delete any document
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check ownership
    require_resource_owner(current_user, document.created_by_id)
    
    db.delete(document)
    db.commit()
    
    return None


@router.delete("/{document_id}/texts/{text_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_text(
    document_id: UUID,
    text_id: UUID,
    current_user: User = Depends(require_contributor),
    db: Session = Depends(get_db)
):
    """
    Delete a specific text (translation) from a document.
    
    - Users can delete their own texts
    - ADMIN can delete any text
    - Cannot delete the last text of a document (delete the document instead)
    """
    text = db.query(Text).filter(
        Text.id == text_id,
        Text.document_id == document_id
    ).first()
    
    if not text:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Text not found"
        )
    
    # Check if this is the last text
    text_count = db.query(func.count(Text.id)).filter(
        Text.document_id == document_id
    ).scalar()
    
    if text_count <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete the last text of a document. Delete the document instead."
        )
    
    # Check ownership
    require_resource_owner(current_user, text.created_by_id)
    
    db.delete(text)
    db.commit()
    
    return None

