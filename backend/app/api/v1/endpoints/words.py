"""
Word management endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app.models.user import User, UserRole
from app.models.word import Word, WordStatus, word_translations
from app.models.language import Language
from app.schemas.word import (
    WordCreate, 
    WordUpdate, 
    Word as WordSchema, 
    WordListItem,
    TranslationCreate,
    TranslationUpdate,
    WordTranslation,
    WordWithTranslations
)
from app.api.deps import (
    get_current_active_user,
    require_contributor,
    require_native_speaker,
    require_admin
)
from app.services.auth_service import require_resource_owner
from sqlalchemy import select, insert, delete, update, and_, or_
from datetime import datetime

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


@router.get("/search", response_model=list[WordWithTranslations])
async def search_words(
    q: str,
    language_ids: str = None,  # Comma-separated list of language UUIDs
    include_translations: bool = True,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Search for words and optionally include their translations.
    
    - q: Search query (searches word and romanization)
    - language_ids: Comma-separated language IDs to search in
    - include_translations: Whether to include translation data
    - Returns words matching the search with their translations
    """
    query = db.query(Word).filter(Word.status == WordStatus.PUBLISHED)
    
    # Apply search filter
    search_filter = or_(
        Word.word.ilike(f"%{q}%"),
        Word.romanization.ilike(f"%{q}%") if q else False
    )
    query = query.filter(search_filter)
    
    # Apply language filter
    if language_ids:
        try:
            lang_id_list = [UUID(lid.strip()) for lid in language_ids.split(",")]
            query = query.filter(Word.language_id.in_(lang_id_list))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid language ID format")
    
    words = query.offset(skip).limit(limit).all()
    
    if not include_translations:
        return words
    
    # Fetch translations for each word
    result = []
    for word in words:
        # Get translation IDs and notes
        translation_rows = db.execute(
            select(
                word_translations.c.translation_id,
                word_translations.c.notes
            ).where(word_translations.c.word_id == word.id)
        ).fetchall()
        
        # Fetch full word details for translations
        translations = []
        for trans_row in translation_rows:
            trans_word = db.query(Word).filter(Word.id == trans_row.translation_id).first()
            if trans_word:
                # Get language name
                lang = db.query(Language).filter(Language.id == trans_word.language_id).first()
                
                translations.append(WordTranslation(
                    id=trans_word.id,
                    word=trans_word.word,
                    romanization=trans_word.romanization,
                    language_id=trans_word.language_id,
                    language_name=lang.name if lang else None,
                    part_of_speech=trans_word.part_of_speech,
                    notes=trans_row.notes
                ))
        
        # Create WordWithTranslations instance
        word_dict = {
            **{c.name: getattr(word, c.name) for c in Word.__table__.columns},
            'translations': translations
        }
        result.append(WordWithTranslations(**word_dict))
    
    return result


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


# ============================================================================
# Translation Endpoints
# ============================================================================

@router.post("/{word_id}/translations/", response_model=WordSchema, status_code=status.HTTP_201_CREATED)
async def add_translation(
    word_id: UUID,
    translation_data: TranslationCreate,
    current_user: User = Depends(require_contributor),
    db: Session = Depends(get_db)
):
    """
    Add a translation link between two words.
    
    Creates a bidirectional relationship: if Word A translates to Word B,
    then Word B translates to Word A.
    
    Requires: NATIVE_SPEAKER, RESEARCHER, or ADMIN role
    """
    # Verify both words exist
    word = db.query(Word).filter(Word.id == word_id).first()
    if not word:
        raise HTTPException(status_code=404, detail="Word not found")
    
    translation = db.query(Word).filter(Word.id == translation_data.translation_id).first()
    if not translation:
        raise HTTPException(status_code=404, detail="Translation word not found")
    
    # Check if words are in different languages
    if word.language_id == translation.language_id:
        raise HTTPException(
            status_code=400,
            detail="Translation must be in a different language"
        )
    
    # Check if translation already exists
    existing = db.execute(
        select(word_translations).where(
            or_(
                and_(
                    word_translations.c.word_id == word_id,
                    word_translations.c.translation_id == translation_data.translation_id
                ),
                and_(
                    word_translations.c.word_id == translation_data.translation_id,
                    word_translations.c.translation_id == word_id
                )
            )
        )
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Translation already exists")
    
    # Add bidirectional translation
    now = datetime.utcnow()
    
    # Forward translation
    db.execute(
        insert(word_translations).values(
            word_id=word_id,
            translation_id=translation_data.translation_id,
            notes=translation_data.notes,
            created_at=now,
            created_by_id=current_user.id
        )
    )
    
    # Reverse translation
    db.execute(
        insert(word_translations).values(
            word_id=translation_data.translation_id,
            translation_id=word_id,
            notes=translation_data.notes,
            created_at=now,
            created_by_id=current_user.id
        )
    )
    
    db.commit()
    db.refresh(word)
    
    return word


@router.delete("/{word_id}/translations/{translation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_translation(
    word_id: UUID,
    translation_id: UUID,
    current_user: User = Depends(require_contributor),
    db: Session = Depends(get_db)
):
    """
    Remove a translation link between two words.
    
    Removes both directions of the relationship.
    
    Requires: NATIVE_SPEAKER, RESEARCHER, or ADMIN role
    """
    # Delete both directions
    result = db.execute(
        delete(word_translations).where(
            or_(
                and_(
                    word_translations.c.word_id == word_id,
                    word_translations.c.translation_id == translation_id
                ),
                and_(
                    word_translations.c.word_id == translation_id,
                    word_translations.c.translation_id == word_id
                )
            )
        )
    )
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Translation not found")
    
    db.commit()
    return None


@router.put("/{word_id}/translations/{translation_id}", response_model=WordSchema)
async def update_translation_notes(
    word_id: UUID,
    translation_id: UUID,
    translation_data: TranslationUpdate,
    current_user: User = Depends(require_contributor),
    db: Session = Depends(get_db)
):
    """
    Update the notes for a translation.
    
    Updates both directions of the relationship with the same notes.
    
    Requires: NATIVE_SPEAKER, RESEARCHER, or ADMIN role
    """
    # Update both directions
    result = db.execute(
        update(word_translations)
        .where(
            or_(
                and_(
                    word_translations.c.word_id == word_id,
                    word_translations.c.translation_id == translation_id
                ),
                and_(
                    word_translations.c.word_id == translation_id,
                    word_translations.c.translation_id == word_id
                )
            )
        )
        .values(notes=translation_data.notes)
    )
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Translation not found")
    
    db.commit()
    
    word = db.query(Word).filter(Word.id == word_id).first()
    return word

