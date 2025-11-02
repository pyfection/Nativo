"""
Document management endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app.models.user import User
from app.models.document import Document, DocumentType
from app.schemas.document import (
    DocumentCreate,
    DocumentUpdate,
    Document as DocumentSchema,
    DocumentListItem
)
from app.api.deps import (
    get_current_active_user,
    require_contributor,
    require_admin
)
from app.services.auth_service import require_resource_owner

router = APIRouter()


@router.get("/", response_model=list[DocumentListItem])
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    language_id: UUID = None,
    document_type: DocumentType = None,
    db: Session = Depends(get_db)
):
    """
    List documents (public access).
    
    - Anyone can view documents
    - Filter by language, type, etc.
    """
    query = db.query(Document)
    
    if language_id:
        query = query.filter(Document.language_id == language_id)
    
    if document_type:
        query = query.filter(Document.document_type == document_type)
    
    documents = query.order_by(Document.created_at.desc()).offset(skip).limit(limit).all()
    
    # Truncate content for list view
    result = []
    for doc in documents:
        doc_dict = {
            'id': doc.id,
            'content': doc.content[:200] if len(doc.content) > 200 else doc.content,
            'document_type': doc.document_type,
            'language_id': doc.language_id,
            'created_at': doc.created_at
        }
        result.append(doc_dict)
    
    return result


@router.get("/{document_id}", response_model=DocumentSchema)
async def get_document(
    document_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a specific document by ID (public access).
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return document


@router.post("/", response_model=DocumentSchema, status_code=status.HTTP_201_CREATED)
async def create_document(
    document_data: DocumentCreate,
    current_user: User = Depends(require_contributor),
    db: Session = Depends(get_db)
):
    """
    Create a new document.
    
    Requires: NATIVE_SPEAKER, RESEARCHER, or ADMIN role
    """
    new_document = Document(
        **document_data.model_dump(),
        created_by_id=current_user.id
    )
    
    db.add(new_document)
    db.commit()
    db.refresh(new_document)
    
    return new_document


@router.put("/{document_id}", response_model=DocumentSchema)
async def update_document(
    document_id: UUID,
    document_data: DocumentUpdate,
    current_user: User = Depends(require_contributor),
    db: Session = Depends(get_db)
):
    """
    Update a document.
    
    - Users can update their own documents
    - ADMIN can update any document
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check ownership (user must own the document or be admin)
    require_resource_owner(current_user, document.created_by_id)
    
    # Update document fields
    for field, value in document_data.model_dump(exclude_unset=True).items():
        setattr(document, field, value)
    
    db.commit()
    db.refresh(document)
    
    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Delete a document (admin only).
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    db.delete(document)
    db.commit()
    
    return None

