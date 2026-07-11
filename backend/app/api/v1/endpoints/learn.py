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
from app.models.word import Lexeme, WordForm
from app.schemas.learning import (
    LearningPathEntry,
    LexemeKnowledgeOut,
    PlacementRequest,
    PlacementResult,
    ReviewCard,
    ReviewTranslation,
    ReviewVerdict,
    TextCompletion,
    TextProgressOut,
)
from app.services import learning_service, lexeme_service

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


@router.get("/{language_id}/review", response_model=list[ReviewCard])
def get_review_deck(
    language_id: UUID,
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """The user's shaky words in this language, as a practice deck."""
    rows = learning_service.get_review_deck(db, current_user.id, language_id, limit=limit)
    if not rows:
        return []

    lexeme_ids = [lexeme.id for _knowledge, lexeme in rows]
    lemma_forms: dict[UUID, WordForm] = {}
    for form in (
        db.query(WordForm)
        .filter(WordForm.lexeme_id.in_(lexeme_ids), WordForm.is_lemma.is_(True))
        .all()
    ):
        lemma_forms[form.lexeme_id] = form

    cards = []
    for knowledge, lexeme in rows:
        form = lemma_forms.get(lexeme.id)
        translations = [
            ReviewTranslation(lemma=link.lemma, language_id=link.language_id)
            for link in lexeme_service.list_translations(db, lexeme.id)
        ]
        cards.append(
            ReviewCard(
                lexeme_id=lexeme.id,
                lemma=lexeme.lemma,
                score=knowledge.score,
                ipa_pronunciation=form.ipa_pronunciation if form else None,
                lemma_form_id=form.id if form else None,
                translations=translations,
            )
        )
    return cards


@router.post("/words/{lexeme_id}/review", response_model=LexemeKnowledgeOut)
def review_word(
    lexeme_id: UUID,
    payload: ReviewVerdict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Record a flashcard verdict: knew it (+1) or didn't (-1)."""
    if db.get(Lexeme, lexeme_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lexeme not found")
    row = learning_service.record_review_result(db, current_user.id, lexeme_id, payload.knew)
    db.commit()
    return row


@router.post("/{language_id}/placement", response_model=PlacementResult)
def apply_placement(
    language_id: UUID,
    payload: PlacementRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Seed frequent words as known from a self-assessed starting level.

    Gap-filling only — existing scores are never lowered, so this is safe
    to run once at signup or later from the learn page.
    """
    if db.get(Language, language_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Language not found")
    seeded = learning_service.apply_placement(db, current_user.id, language_id, payload.level)
    db.commit()
    return PlacementResult(seeded=seeded)


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
