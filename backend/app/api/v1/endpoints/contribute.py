"""
Quick Contribute endpoints: the task deck and the one answer that has no
existing endpoint (define a word with its meaning in one step).

The other cards are answered through the endpoints they already have:
audio upload, link update, word verify/reject, and proposal votes.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.models.language import Language
from app.models.user import User
from app.schemas.contribute import ContributeTask, DefineWordAnswer, DefineWordResult
from app.services import contribute_service

router = APIRouter()

# Skipped keys a client may send back; older ones simply come round again.
MAX_EXCLUDED = 200


@router.get("/{language_id}/tasks", response_model=list[ContributeTask])
def get_tasks(
    language_id: UUID,
    limit: int = Query(10, ge=1, le=30),
    exclude: list[str] = Query([], description="Keys of cards skipped this session"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """A varied deck of small tasks the user can do in this language."""
    if db.get(Language, language_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Language not found")
    return contribute_service.build_deck(
        db, current_user, language_id, limit=limit, exclude=exclude[-MAX_EXCLUDED:]
    )


@router.post(
    "/{language_id}/define",
    response_model=DefineWordResult,
    status_code=status.HTTP_201_CREATED,
)
def define_word(
    language_id: UUID,
    answer: DefineWordAnswer,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Add a word seen in a text, with its meaning. Editors publish it;
    anyone else's lands in the review queue."""
    lexeme = contribute_service.define_word(db, current_user, language_id, answer)
    return DefineWordResult(lexeme_id=lexeme.id, status=lexeme.status)
