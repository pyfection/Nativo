"""
Statistics endpoint for platform-wide metrics.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct

from app.api.deps import get_db
from app.models.language import Language
from app.models.word.word import Word
from app.models.audio import Audio
from app.models.document import Document
from app.models.user import User

router = APIRouter()


@router.get("/")
def get_statistics(db: Session = Depends(get_db)):
    """
    Get platform-wide statistics for the landing page.
    
    Returns:
    - total_languages: Count of all languages
    - total_words: Count of all words
    - total_audio: Count of all audio recordings
    - total_documents: Count of all documents
    - total_contributors: Count of users who have contributed at least one word or document
    """
    # Count languages
    total_languages = db.query(func.count(Language.id)).scalar() or 0
    
    # Count words
    total_words = db.query(func.count(Word.id)).scalar() or 0
    
    # Count audio recordings
    total_audio = db.query(func.count(Audio.id)).scalar() or 0
    
    # Count documents
    total_documents = db.query(func.count(Document.id)).scalar() or 0
    
    # Count contributors (users who created at least one word or document)
    word_contributors = db.query(distinct(Word.created_by_id)).subquery()
    document_contributors = db.query(distinct(Document.created_by_id)).subquery()
    
    # Union the two sets and count unique contributors
    total_contributors = db.query(
        func.count(distinct(User.id))
    ).filter(
        (User.id.in_(db.query(Word.created_by_id).distinct())) |
        (User.id.in_(db.query(Document.created_by_id).distinct()))
    ).scalar() or 0
    
    return {
        "total_languages": total_languages,
        "total_words": total_words,
        "total_audio": total_audio,
        "total_documents": total_documents,
        "total_contributors": total_contributors,
    }

