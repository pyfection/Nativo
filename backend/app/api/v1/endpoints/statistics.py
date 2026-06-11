"""
Statistics endpoint for platform-wide and per-language metrics.
"""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import distinct, func
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.audio import Audio
from app.models.document import Document
from app.models.language import Language
from app.models.text import Text
from app.models.user import User
from app.models.user_language import UserLanguage
from app.models.word.associations import word_audio
from app.models.word.word import Word

router = APIRouter()


@router.get("/")
def get_statistics(language_id: UUID | None = None, db: Session = Depends(get_db)):
    """
    Get statistics for the landing page.

    Without `language_id`: platform-wide totals (every count is global).
    With `language_id`: per-language totals — counts only what's linked to
    that language. `total_languages` stays at 1 (the language itself) so
    the response shape doesn't change.
    """
    if language_id is None:
        return _platform_stats(db)
    return _language_stats(db, language_id)


def _platform_stats(db: Session) -> dict:
    total_languages = db.query(func.count(Language.id)).scalar() or 0
    total_words = db.query(func.count(Word.id)).scalar() or 0
    total_audio = db.query(func.count(Audio.id)).scalar() or 0
    total_documents = db.query(func.count(Document.id)).scalar() or 0
    total_contributors = (
        db.query(func.count(distinct(User.id)))
        .filter(
            (User.id.in_(db.query(Word.created_by_id).distinct()))
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
    # Words: direct language_id link.
    total_words = (
        db.query(func.count(Word.id)).filter(Word.language_id == language_id).scalar() or 0
    )

    # Documents: distinct Documents that group at least one Text in this language.
    total_documents = (
        db.query(func.count(distinct(Text.document_id)))
        .filter(Text.language_id == language_id, Text.document_id.is_not(None))
        .scalar()
        or 0
    )

    # Audio: distinct audio rows linked to words in this language via word_audio.
    total_audio = (
        db.query(func.count(distinct(word_audio.c.audio_id)))
        .join(Word, Word.id == word_audio.c.word_id)
        .filter(Word.language_id == language_id)
        .scalar()
        or 0
    )

    # Contributors:
    #   - users with a UserLanguage row for this language, OR
    #   - users who created a Word in this language, OR
    #   - users who created a Text in this language.
    word_creator_ids = (
        db.query(Word.created_by_id).filter(Word.language_id == language_id).distinct()
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
