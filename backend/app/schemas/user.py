"""
User schemas for API request/response validation.
"""
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID

from app.models.user import UserRole


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)


class UserCreate(UserBase):
    """Schema for creating a new user"""
    password: str = Field(..., min_length=8, max_length=100)
    role: Optional[UserRole] = UserRole.PUBLIC


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class UserResponse(UserBase):
    """Schema for user response (no password)"""
    id: UUID
    role: UserRole
    is_active: bool
    is_superuser: bool
    created_at: datetime
    language_proficiencies: Optional[List["LanguageProficiencyResponse"]] = None
    
    model_config = ConfigDict(from_attributes=True)


# Import here to avoid circular dependency
from app.schemas.user_language import LanguageProficiencyResponse
UserResponse.model_rebuild()


class UserUpdate(BaseModel):
    """Schema for updating user information"""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class Token(BaseModel):
    """Schema for JWT token response"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for decoded token data"""
    user_id: UUID
    role: UserRole


class PasswordResetRequest(BaseModel):
    """
    Schema for requesting a password reset.
    
    When a user requests a password reset, they provide their email address.
    If the email exists in the system, a reset token will be sent to that email.
    
    **Example:**
    ```json
    {
        "email": "user@example.com"
    }
    ```
    """
    email: EmailStr = Field(
        ...,
        description="Email address of the user requesting password reset. Must be a valid email format.",
        examples=["user@example.com", "john.doe@example.org"]
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com"
            }
        }
    )


class PasswordReset(BaseModel):
    """
    Schema for resetting a password using a reset token.
    
    The user receives a reset token via email and uses it along with their new password
    to reset their account password.
    
    **Example:**
    ```json
    {
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiMTIzNDU2NzgtMTIzNC0xMjM0LTEyMzQtMTIzNDU2Nzg5MDEyIiwiZXhwIjoxNjAwMDAwMDAwfQ.example_signature",
        "new_password": "newSecurePassword123"
    }
    ```
    """
    token: str = Field(
        ...,
        min_length=10,
        description="Password reset token received via email. This is a JWT token that contains user identification and expiration information.",
        examples=[
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiMTIzNDU2NzgtMTIzNC0xMjM0LTEyMzQtMTIzNDU2Nzg5MDEyIiwiZXhwIjoxNjAwMDAwMDAwfQ.example_signature"
        ]
    )
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="New password for the user account. Must be at least 8 characters long and no more than 100 characters.",
        examples=["newSecurePassword123", "MyNewP@ssw0rd!"]
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiMTIzNDU2NzgtMTIzNC0xMjM0LTEyMzQtMTIzNDU2Nzg5MDEyIiwiZXhwIjoxNjAwMDAwMDAwfQ.example_signature",
                "new_password": "newSecurePassword123"
            }
        }
    )


class PasswordResetResponse(BaseModel):
    """
    Schema for password reset response messages.
    
    **Example:**
    ```json
    {
        "message": "Password reset email sent successfully"
    }
    ```
    """
    message: str = Field(
        ...,
        description="Response message indicating the result of the password reset operation. This message confirms that the operation was processed.",
        examples=[
            "Password reset email sent successfully",
            "Password has been reset successfully"
        ]
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "message": "Password reset email sent successfully"
                },
                {
                    "message": "Password has been reset successfully"
                }
            ]
        }
    )

