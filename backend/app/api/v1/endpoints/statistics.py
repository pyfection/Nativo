"""
Statistics endpoint for platform-wide and per-language metrics.

`total_words` historically counts dictionary entries; with the Lexeme/WordForm
split that's now Lexeme count, not WordForm count.
"""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import distinct, func
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.audio import Audio
from app.models.document import Document
from app.models.language import Language
from app.models.text import Text, TextStatus
from app.models.user import User
from app.models.user_language import UserLanguage
from app.models.word import Lexeme, WordForm, word_form_audio

router = APIRouter()


@router.get("/")
def get_statistics(language_id: UUID | None = None, db: Session = Depends(get_db)):
    if language_id is None:
        return _platform_stats(db)
    return _language_stats(db, language_id)


def _platform_stats(db: Session) -> dict:
    total_languages = db.query(func.count(Language.id)).scalar() or 0
    total_words = db.query(func.count(Lexeme.id)).scalar() or 0
    total_audio = db.query(func.count(Audio.id)).scalar() or 0
    total_documents = db.query(func.count(Document.id)).scalar() or 0
    total_contributors = (
        db.query(func.count(distinct(User.id)))
        .filter(
            (User.id.in_(db.query(Lexeme.created_by_id).distinct()))
            | (User.id.in_(db.query(Document.created_by_id).distinct()))
        )
        .scalar()
        or 0
    )
    return {
        "total_languages": total_languages,
        "total_words": total_words,
        "total_audio": total_audio,
        "total_documents": total_documents,
        "total_contributors": total_contributors,
    }


def _language_stats(db: Session, language_id: UUID) -> dict:
    total_words = (
        db.query(func.count(Lexeme.id))
        .filter(Lexeme.language_id == language_id)
        .scalar()
        or 0
    )

    total_documents = (
        db.query(func.count(distinct(Text.document_id)))
        .filter(
            Text.language_id == language_id,
            Text.document_id.is_not(None),
            Text.status == TextStatus.PUBLISHED,
        )
        .scalar()
        or 0
    )

    total_audio = (
        db.query(func.count(distinct(word_form_audio.c.audio_id)))
        .join(WordForm, WordForm.id == word_form_audio.c.word_form_id)
        .join(Lexeme, Lexeme.id == WordForm.lexeme_id)
        .filter(Lexeme.language_id == language_id)
        .scalar()
        or 0
    )

    word_creator_ids = (
        db.query(Lexeme.created_by_id).filter(Lexeme.language_id == language_id).distinct()
    )
    text_creator_ids = (
        db.query(Text.created_by_id).filter(Text.language_id == language_id).distinct()
    )
    proficiency_user_ids = (
        db.query(UserLanguage.user_id).filter(UserLanguage.language_id == language_id).distinct()
    )
    total_contributors = (
        db.query(func.count(distinct(User.id)))
        .filter(
            User.id.in_(word_creator_ids)
            | User.id.in_(text_creator_ids)
            | User.id.in_(proficiency_user_ids)
        )
        .scalar()
        or 0
    )

    return {
        "total_languages": 1,
        "total_words": total_words,
        "total_audio": total_audio,
        "total_documents": total_documents,
        "total_contributors": total_contributors,
    }
