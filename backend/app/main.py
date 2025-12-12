"""
Main FastAPI application for Nativo endangered language preservation platform.
"""
import logging
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.config import settings
from app.api.v1.router import router as api_v1_router
from app.admin import create_admin
from app.database import SessionLocal
from app.services.token_cleanup_service import token_cleanup_service

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Set specific loggers
logging.getLogger("uvicorn").setLevel(logging.INFO)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None


def cleanup_password_reset_tokens():
    """
    Background task to clean up expired and old password reset tokens.
    
    This function is called periodically by the scheduler to remove
    expired tokens and old used tokens from the database.
    """
    db = SessionLocal()
    try:
        result = token_cleanup_service.cleanup_all_expired_and_old(db, old_used_days=7)
        logger.info(
            f"Token cleanup completed: {result['total_deleted']} tokens deleted "
            f"({result['expired_tokens_deleted']} expired, {result['old_used_tokens_deleted']} old used)"
        )
    except Exception as e:
        logger.error(
            f"Error during token cleanup: {str(e)}",
            extra={"error": str(e)},
            exc_info=True
        )
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    
    Handles startup and shutdown tasks, including scheduler initialization.
    """
    # Startup
    global scheduler
    
    logger.info(f"Starting {settings.APP_NAME} application")
    
    # Initialize and start scheduler
    scheduler = BackgroundScheduler()
    
    # Schedule token cleanup to run every 6 hours
    scheduler.add_job(
        cleanup_password_reset_tokens,
        trigger=IntervalTrigger(hours=6),
        id="cleanup_password_reset_tokens",
        name="Cleanup expired password reset tokens",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Background scheduler started for token cleanup")
    
    # Run initial cleanup on startup
    try:
        cleanup_password_reset_tokens()
    except Exception as e:
        logger.warning(
            f"Initial token cleanup failed: {str(e)}",
            extra={"error": str(e)}
        )
    
    yield
    
    # Shutdown
    if scheduler:
        scheduler.shutdown()
        logger.info("Background scheduler stopped")


# Create FastAPI application with lifespan
app = FastAPI(
    title=settings.APP_NAME,
    description="A platform for preserving endangered languages through digital archival",
    version="0.1.0",
    lifespan=lifespan,
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

