"""
Language management endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app.models.user import User, UserRole
from app.models.language import Language
from app.schemas.language import (
    LanguageCreate,
    LanguageUpdate,
    Language as LanguageSchema,
    LanguageListItem
)
from app.api.deps import (
    get_current_active_user,
    require_admin,
    require_role
)

router = APIRouter()


@router.get("/", response_model=list[LanguageListItem])
async def list_languages(
    skip: int = 0,
    limit: int = 100,
    is_endangered: bool = None,
    db: Session = Depends(get_db)
):
    """
    List all languages (public access).
    
    - Anyone can view languages
    - Filter by endangered status
    """
    query = db.query(Language)
    
    if is_endangered is not None:
        query = query.filter(Language.is_endangered == is_endangered)
    
    languages = query.offset(skip).limit(limit).all()
    return languages


@router.get("/{language_id}", response_model=LanguageSchema)
async def get_language(
    language_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a specific language by ID (public access).
    """
    language = db.query(Language).filter(Language.id == language_id).first()
    
    if not language:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Language not found"
        )
    
    return language


@router.post("/", response_model=LanguageSchema, status_code=status.HTTP_201_CREATED)
async def create_language(
    language_data: LanguageCreate,
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.RESEARCHER)),
    db: Session = Depends(get_db)
):
    """
    Create a new language.
    
    Requires: ADMIN or RESEARCHER role
    """
    # Check if language with same name already exists
    existing = db.query(Language).filter(Language.name == language_data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Language with this name already exists"
        )
    
    # Check if ISO code already exists (if provided)
    if language_data.iso_639_3:
        existing_iso = db.query(Language).filter(
            Language.iso_639_3 == language_data.iso_639_3
        ).first()
        if existing_iso:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Language with this ISO 639-3 code already exists"
            )
    
    new_language = Language(**language_data.model_dump())
    
    db.add(new_language)
    db.commit()
    db.refresh(new_language)
    
    return new_language


@router.put("/{language_id}", response_model=LanguageSchema)
async def update_language(
    language_id: UUID,
    language_data: LanguageUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Update a language (admin only).
    
    Can update any field including theme colors.
    """
    language = db.query(Language).filter(Language.id == language_id).first()
    
    if not language:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Language not found"
        )
    
    # Check for duplicate name if updating name
    if language_data.name and language_data.name != language.name:
        existing = db.query(Language).filter(Language.name == language_data.name).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Language with this name already exists"
            )
    
    # Check for duplicate ISO code if updating
    if language_data.iso_639_3 and language_data.iso_639_3 != language.iso_639_3:
        existing_iso = db.query(Language).filter(
            Language.iso_639_3 == language_data.iso_639_3
        ).first()
        if existing_iso:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Language with this ISO 639-3 code already exists"
            )
    
    # Update language fields
    for field, value in language_data.model_dump(exclude_unset=True).items():
        setattr(language, field, value)
    
    db.commit()
    db.refresh(language)
    
    return language


@router.delete("/{language_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_language(
    language_id: UUID,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Delete a language (admin only).
    
    Warning: This will fail if there are words or documents associated with this language.
    """
    language = db.query(Language).filter(Language.id == language_id).first()
    
    if not language:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Language not found"
        )
    
    try:
        db.delete(language)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete language with existing words or documents"
        )
    
    return None
