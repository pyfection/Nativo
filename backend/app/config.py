from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables (or .env file)."""

    # Application
    APP_NAME: str = "Nativo"
    DEBUG: bool = False

    # Security — must be provided. Generate with: openssl rand -hex 32
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Database — must be a Postgres URL. Alembic migrations use Postgres-only
    # syntax and will fail against SQLite.
    DATABASE_URL: str

    # CORS — list of allowed origins. Use ["*"] for fully-open dev only.
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    # Where account emails (password reset, verification) link back to.
    FRONTEND_URL: str = "http://localhost:5173"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()
