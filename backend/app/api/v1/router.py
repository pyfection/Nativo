"""
Main API router that includes all endpoint routers.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    activity,
    audio,
    auth,
    contributors,
    documents,
    languages,
    learn,
    statistics,
    text_links,
    user_languages,
    users,
    words,
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
router.include_router(activity.router, prefix="/activity", tags=["Activity"])
router.include_router(learn.router, prefix="/learn", tags=["Learn"])
router.include_router(contributors.router, prefix="/contributors", tags=["Contributors"])
