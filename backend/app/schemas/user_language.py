"""
User-Language proficiency schemas for API request/response validation.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID

from app.models.user_language import ProficiencyLevel


class UserLanguageCreate(BaseModel):
    """Schema for creating a user-language proficiency relationship"""
    language_id: UUID
    proficiency_level: ProficiencyLevel
    can_edit: Optional[bool] = False  # Defaults to False, can be set by admin
    can_verify: Optional[bool] = False  # Defaults to False, can be set by admin


class UserLanguageUpdate(BaseModel):
    """Schema for updating user-language proficiency (admin only for permissions)"""
    proficiency_level: Optional[ProficiencyLevel] = None
    can_edit: Optional[bool] = None
    can_verify: Optional[bool] = None


class LanguageInfo(BaseModel):
    """Minimal language information for nested responses"""
    id: UUID
    name: str
    native_name: Optional[str] = None
    iso_639_3: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class UserLanguageResponse(BaseModel):
    """Full user-language proficiency response with language details"""
    user_id: UUID
    language_id: UUID
    proficiency_level: ProficiencyLevel
    can_edit: bool
    can_verify: bool
    created_at: datetime
    language: Optional[LanguageInfo] = None
    
    model_config = ConfigDict(from_attributes=True)


class LanguageProficiencyResponse(BaseModel):
    """User-language proficiency for nested in user responses"""
    language_id: UUID
    proficiency_level: ProficiencyLevel
    can_edit: bool
    can_verify: bool
    created_at: datetime
    language: Optional[LanguageInfo] = None
    
    model_config = ConfigDict(from_attributes=True)


class UserInfo(BaseModel):
    """Minimal user information for nested responses"""
    id: UUID
    username: str
    email: str
    
    model_config = ConfigDict(from_attributes=True)


class LanguageUserResponse(BaseModel):
    """Response for users of a specific language"""
    user_id: UUID
    language_id: UUID
    proficiency_level: ProficiencyLevel
    can_edit: bool
    can_verify: bool
    created_at: datetime
    user: Optional[UserInfo] = None
    
    model_config = ConfigDict(from_attributes=True)

