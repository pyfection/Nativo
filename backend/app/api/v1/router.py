"""
Main API router that includes all endpoint routers.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    users,
    languages,
    words,
    documents,
    audio,
    statistics,
    user_languages,
    text_links,
)

router = APIRouter()

# Include all endpoint routers
router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
router.include_router(users.router, prefix="/users", tags=["Users"])
router.include_router(languages.router, prefix="/languages", tags=["Languages"])
router.include_router(user_languages.router, tags=["User Languages"])
router.include_router(words.router, prefix="/words", tags=["Words"])
router.include_router(documents.router, prefix="/documents", tags=["Documents"])
router.include_router(text_links.router, tags=["Text Links"])
router.include_router(audio.router, prefix="/audio", tags=["Audio"])
router.include_router(statistics.router, prefix="/statistics", tags=["Statistics"])

