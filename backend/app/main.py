"""
Main FastAPI application for Nativo endangered language preservation platform.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.api.v1.router import router as api_v1_router
from app.admin import create_admin

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="A platform for preserving endangered languages through digital archival",
    version="0.1.0",
)

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

# Mount admin interface
create_admin(app)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Nativo API",
        "docs": "/docs",
        "admin": "/admin",
        "version": "0.1.0"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

