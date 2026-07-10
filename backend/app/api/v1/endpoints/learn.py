"""
Guided learning path endpoints.

Reading the path is public (anonymous visitors see the cold-start line and
can sign up to keep their place); recording clicks and completions requires
an account, since that's what personalisation is.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_current_user_optional, get_db
from app.limiter import limiter
from app.models.language import Language
from app.models.learning import UserLexemeKnowledge
from app.models.text import Text
from app.models.user import User
from app.models.word import Lexeme
from app.schemas.learning import (
    LearningPathEntry,
    LexemeKnowledgeOut,
    TextCompletion,
    TextProgressOut,
)
from app.services import learning_service

router = APIRouter()


@router.get("/{language_id}/path", response_model=list[LearningPathEntry])
@limiter.limit("30/minute")
def get_path(
    request: Request,
    language_id: UUID,
    limit: int = Query(20, ge=1, le=100),
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """The learner's ordered line through the language's texts."""
    if db.get(Language, language_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Language not found")
    return learning_service.get_learning_path(
        db,
        language_id,
        user_id=current_user.id if current_user else None,
        limit=limit,
    )


@router.get("/{language_id}/words", response_model=list[LexemeKnowledgeOut])
def get_word_knowledge(
    language_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """All of the user's scored lexemes in this language (feeds highlighting)."""
    return (
        db.query(UserLexemeKnowledge)
        .join(Lexeme, Lexeme.id == UserLexemeKnowledge.lexeme_id)
        .filter(
            UserLexemeKnowledge.user_id == current_user.id,
            Lexeme.language_id == language_id,
        )
        .all()
    )


@router.post("/words/{lexeme_id}/click", response_model=LexemeKnowledgeOut)
def click_word(
    lexeme_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """The reader tapped a word to look it up — a \"don't know yet\" signal."""
    if db.get(Lexeme, lexeme_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lexeme not found")
    row = learning_service.record_click(db, current_user.id, lexeme_id)
    db.commit()
    return row


@router.post("/texts/{text_id}/complete", response_model=TextProgressOut)
def complete_text(
    text_id: UUID,
    payload: TextCompletion,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Finish a text: store the difficulty verdict and apply the know-bonus."""
    text = db.get(Text, text_id)
    if text is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Text not found")
    progress = learning_service.complete_text(
        db,
        current_user.id,
        text,
        payload.difficulty_rating,
        clicked_lexeme_ids=set(payload.clicked_lexeme_ids),
    )
    db.commit()
    return progress
