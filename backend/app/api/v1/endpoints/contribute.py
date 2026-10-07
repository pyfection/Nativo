"""
Quick Contribute endpoints: the task deck, the answers that have no
existing endpoint (define a word, confirm an outside spelling, translate a
word or text), and adding outside source text.

The other cards are answered through the endpoints they already have:
audio upload, link update, word verify/reject, proposal votes and reviews.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.models.language import Language
from app.models.user import User
from app.schemas.contribute import (
    ContributeResult,
    ContributeTask,
    DefineWordAnswer,
    DefineWordResult,
    SourceTextCreate,
    SourceTextResult,
    SpellingAnswer,
    TranslateTextAnswer,
    TranslateWordAnswer,
)
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


@router.post("/{language_id}/spelling", response_model=ContributeResult)
def confirm_spelling(
    language_id: UUID,
    answer: SpellingAnswer,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Give the standard spelling of a word an outside source writes its own
    way. Known words gain the source's spelling as a variant; unknown ones
    become new words."""
    return contribute_service.confirm_spelling(db, current_user, language_id, answer)


@router.post("/{language_id}/translate-word", response_model=ContributeResult)
def translate_word(
    language_id: UUID,
    answer: TranslateWordAnswer,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Translate a word from another language into this one."""
    return contribute_service.translate_word(db, current_user, language_id, answer)


@router.post("/{language_id}/translate-text", response_model=ContributeResult)
def translate_text(
    language_id: UUID,
    answer: TranslateTextAnswer,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Translate a short text (internal, or an outside snippet) into this
    language."""
    return contribute_service.translate_text(db, current_user, language_id, answer)


@router.post(
    "/{language_id}/sources",
    response_model=SourceTextResult,
    status_code=status.HTTP_201_CREATED,
)
def add_source_text(
    language_id: UUID,
    data: SourceTextCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Store text from an outside page (in this language) as sentence
    snippets for spelling and translation cards. Editors of the language
    only; the server stores what it's given and never fetches the URL."""
    created = contribute_service.add_source_text(db, current_user, language_id, data)
    return SourceTextResult(created=created)
