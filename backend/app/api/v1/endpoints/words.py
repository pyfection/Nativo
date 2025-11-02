"""
Word management endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app.models.user import User, UserRole
from app.models.word import Word, WordStatus
from app.schemas.word import WordCreate, WordUpdate, Word as WordSchema, WordListItem
from app.api.deps import (
    get_current_active_user,
    require_contributor,
    require_native_speaker,
    require_admin
)
from app.services.auth_service import require_resource_owner

router = APIRouter()


@router.get("/", response_model=list[WordListItem])
async def list_words(
    skip: int = 0,
    limit: int = 100,
    language_id: UUID = None,
    status_filter: WordStatus = None,
    db: Session = Depends(get_db)
):
    """
    List words (public access).
    
    - Anyone can view published words
    - Filter by language, status, etc.
    """
    query = db.query(Word)
    
    if language_id:
        query = query.filter(Word.language_id == language_id)
    
    if status_filter:
        query = query.filter(Word.status == status_filter)
    else:
        # By default, show only published words to public
        query = query.filter(Word.status == WordStatus.PUBLISHED)
    
    words = query.offset(skip).limit(limit).all()
    return words


@router.get("/{word_id}", response_model=WordSchema)
async def get_word(
    word_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a specific word by ID (public access for published words).
    """
    word = db.query(Word).filter(Word.id == word_id).first()
    
    if not word:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Word not found"
        )
    
    return word


@router.post("/", response_model=WordSchema, status_code=status.HTTP_201_CREATED)
async def create_word(
    word_data: WordCreate,
    current_user: User = Depends(require_contributor),
    db: Session = Depends(get_db)
):
    """
    Create a new word.
    
    Requires: NATIVE_SPEAKER, RESEARCHER, or ADMIN role
    """
    new_word = Word(
        **word_data.model_dump(exclude_unset=True),
        created_by_id=current_user.id
    )
    
    db.add(new_word)
    db.commit()
    db.refresh(new_word)
    
    return new_word


@router.put("/{word_id}", response_model=WordSchema)
async def update_word(
    word_id: UUID,
    word_data: WordUpdate,
    current_user: User = Depends(require_contributor),
    db: Session = Depends(get_db)
):
    """
    Update a word.
    
    - Users can update their own words
    - ADMIN can update any word
    """
    word = db.query(Word).filter(Word.id == word_id).first()
    
    if not word:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Word not found"
        )
    
    # Check ownership (user must own the word or be admin)
    require_resource_owner(current_user, word.created_by_id)
    
    # Update word fields
    for field, value in word_data.model_dump(exclude_unset=True).items():
        setattr(word, field, value)
    
    db.commit()
    db.refresh(word)
    
    return word


@router.delete("/{word_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_word(
    word_id: UUID,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Delete a word (admin only).
    """
    word = db.query(Word).filter(Word.id == word_id).first()
    
    if not word:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Word not found"
        )
    
    db.delete(word)
    db.commit()
    
    return None


@router.post("/{word_id}/verify", response_model=WordSchema)
async def verify_word(
    word_id: UUID,
    current_user: User = Depends(require_native_speaker),
    db: Session = Depends(get_db)
):
    """
    Verify a word as accurate.
    
    Requires: NATIVE_SPEAKER or ADMIN role
    """
    word = db.query(Word).filter(Word.id == word_id).first()
    
    if not word:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Word not found"
        )
    
    word.is_verified = True
    word.verified_by_id = current_user.id
    word.status = WordStatus.PUBLISHED
    
    db.commit()
    db.refresh(word)
    
    return word

