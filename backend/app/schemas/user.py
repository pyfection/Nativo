"""
User schemas for API request/response validation.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class UserBase(BaseModel):
    """Base user schema"""

    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)


class UserCreate(UserBase):
    """Schema for creating a new user"""

    password: str = Field(..., min_length=8, max_length=100)
    role: UserRole | None = UserRole.PUBLIC


class UserLogin(BaseModel):
    """Schema for user login"""

    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    """Request a password-reset email."""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Set a new password using an emailed reset token."""

    token: str
    new_password: str = Field(..., min_length=8, max_length=100)


class VerifyEmailRequest(BaseModel):
    """Confirm an email address using an emailed verification token."""

    token: str


class UserResponse(UserBase):
    """Schema for user response (no password)"""

    id: UUID
    role: UserRole
    is_active: bool
    is_superuser: bool
    email_verified_at: datetime | None = None
    created_at: datetime
    language_proficiencies: list["LanguageProficiencyResponse"] | None = None

    model_config = ConfigDict(from_attributes=True)


# Import here to avoid circular dependency
from app.schemas.user_language import LanguageProficiencyResponse  # noqa: E402

UserResponse.model_rebuild()


class UserUpdate(BaseModel):
    """Schema for updating user information"""

    email: EmailStr | None = None
    username: str | None = Field(None, min_length=3, max_length=100)
    password: str | None = Field(None, min_length=8, max_length=100)
    role: UserRole | None = None
    is_active: bool | None = None


class Token(BaseModel):
    """Schema for JWT token response"""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for decoded token data"""

    user_id: UUID
    role: UserRole


class ApiTokenCreate(BaseModel):
    """Request a new personal API token."""

    name: str = Field(..., min_length=1, max_length=100)


class ApiTokenResponse(BaseModel):
    """A personal API token as listed — never includes the secret."""

    id: UUID
    name: str
    token_prefix: str
    created_at: datetime
    last_used_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ApiTokenCreated(ApiTokenResponse):
    """Returned once, at creation: the only time the plaintext is visible."""

    token: str
