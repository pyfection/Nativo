"""
Main FastAPI application for Nativo endangered language preservation platform.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.sessions import SessionMiddleware

from app.admin import create_admin
from app.api.v1.router import router as api_v1_router
from app.config import settings
from app.limiter import limiter
from app.utils.file_storage import UPLOADS_ROOT, presigned_url, s3_bucket

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="A platform for preserving endangered languages through digital archival",
    version="0.1.0",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS
# Use ["*"] to allow all origins (development only)
# Note: allow_credentials must be False when using ["*"]
cors_origins = settings.BACKEND_CORS_ORIGINS
allow_creds = "*" not in cors_origins if isinstance(cors_origins, list) else cors_origins != ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=allow_creds,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add session middleware for admin authentication
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie="nativo_session",
    max_age=14400,  # 4 hours
)

# Include API router
app.include_router(api_v1_router, prefix="/api/v1")

# Serve user-uploaded files (audio recordings, future image attachments)
# from /uploads/* so Audio rows can store a directly-fetchable URL path.
# With object storage configured (BUCKET_NAME set — Tigris/S3/R2), the same
# path 307-redirects to a short-lived presigned URL, so the bucket stays
# private and stored file_paths never change. Without it, files come off
# local disk (dev, or the Fly volume when mounted).
if s3_bucket():

    @app.get("/uploads/{key:path}", include_in_schema=False)
    async def serve_upload(key: str):
        from fastapi.responses import RedirectResponse

        return RedirectResponse(presigned_url(key), status_code=307)

else:
    UPLOADS_ROOT.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=UPLOADS_ROOT), name="uploads")

# Mount admin interface
create_admin(app)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Nativo API",
        "docs": "/docs",
        "admin": "/admin",
        "version": "0.1.0",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
