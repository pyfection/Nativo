"""
User-Language proficiency management endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from uuid import UUID
from typing import List, Optional

from app.api.deps import get_db, get_current_active_user, require_admin
from app.models.user import User
from app.models.user_language import UserLanguage, ProficiencyLevel
from app.models.language import Language
from app.schemas.user_language import (
    UserLanguageCreate,
    UserLanguageUpdate,
    UserLanguageResponse,
    LanguageUserResponse,
)

router = APIRouter()


@router.post("/users/{user_id}/languages/", response_model=UserLanguageResponse, status_code=status.HTTP_201_CREATED)
def add_user_language(
    user_id: UUID,
    data: UserLanguageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Add a language proficiency for a user.
    Users can add their own proficiencies with default permissions (False).
    Admins can add proficiencies for any user and set permissions.
    """
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check permissions: users can only add their own, admins can add for anyone
    if current_user.id != user_id and current_user.role.value != "admin":
        raise HTTPException(
            status_code=403,
            detail="You can only manage your own language proficiencies"
        )
    
    # Check if language exists
    language = db.query(Language).filter(Language.id == data.language_id).first()
    if not language:
        raise HTTPException(status_code=404, detail="Language not found")
    
    # Check if relationship already exists
    existing = db.query(UserLanguage).filter(
        and_(
            UserLanguage.user_id == user_id,
            UserLanguage.language_id == data.language_id
        )
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="User already has a proficiency record for this language"
        )
    
    # Only admins can set permissions
    can_edit = data.can_edit if current_user.role.value == "admin" else False
    can_verify = data.can_verify if current_user.role.value == "admin" else False
    
    # Create the relationship
    user_language = UserLanguage(
        user_id=user_id,
        language_id=data.language_id,
        proficiency_level=data.proficiency_level,
        can_edit=can_edit,
        can_verify=can_verify
    )
    
    db.add(user_language)
    db.commit()
    db.refresh(user_language)
    
    return user_language


@router.get("/users/{user_id}/languages/", response_model=List[UserLanguageResponse])
def get_user_languages(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all language proficiencies for a user."""
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    proficiencies = db.query(UserLanguage).filter(
        UserLanguage.user_id == user_id
    ).all()
    
    return proficiencies


@router.put("/users/{user_id}/languages/{language_id}", response_model=UserLanguageResponse)
def update_user_language(
    user_id: UUID,
    language_id: UUID,
    data: UserLanguageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update a user-language proficiency.
    Users can update their own proficiency level.
    Only admins can update permissions.
    """
    # Get the relationship
    user_language = db.query(UserLanguage).filter(
        and_(
            UserLanguage.user_id == user_id,
            UserLanguage.language_id == language_id
        )
    ).first()
    
    if not user_language:
        raise HTTPException(
            status_code=404,
            detail="User language proficiency not found"
        )
    
    # Check permissions
    is_admin = current_user.role.value == "admin"
    is_own_record = current_user.id == user_id
    
    if not is_own_record and not is_admin:
        raise HTTPException(
            status_code=403,
            detail="You can only update your own language proficiencies"
        )
    
    # Update proficiency level (users and admins can do this)
    if data.proficiency_level is not None:
        user_language.proficiency_level = data.proficiency_level
    
    # Update permissions (only admins can do this)
    if data.can_edit is not None:
        if not is_admin:
            raise HTTPException(
                status_code=403,
                detail="Only admins can update edit permissions"
            )
        user_language.can_edit = data.can_edit
    
    if data.can_verify is not None:
        if not is_admin:
            raise HTTPException(
                status_code=403,
                detail="Only admins can update verify permissions"
            )
        user_language.can_verify = data.can_verify
    
    db.commit()
    db.refresh(user_language)
    
    return user_language


@router.delete("/users/{user_id}/languages/{language_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_language(
    user_id: UUID,
    language_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Remove a language proficiency from a user.
    Users can remove their own proficiencies.
    Admins can remove any proficiency.
    """
    # Get the relationship
    user_language = db.query(UserLanguage).filter(
        and_(
            UserLanguage.user_id == user_id,
            UserLanguage.language_id == language_id
        )
    ).first()
    
    if not user_language:
        raise HTTPException(
            status_code=404,
            detail="User language proficiency not found"
        )
    
    # Check permissions
    if current_user.id != user_id and current_user.role.value != "admin":
        raise HTTPException(
            status_code=403,
            detail="You can only remove your own language proficiencies"
        )
    
    db.delete(user_language)
    db.commit()
    
    return None


@router.get("/languages/{language_id}/users/", response_model=List[LanguageUserResponse])
def get_language_users(
    language_id: UUID,
    proficiency: Optional[ProficiencyLevel] = None,
    can_edit: Optional[bool] = None,
    can_verify: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all users for a specific language with optional filters.
    Useful for finding native speakers, editors, verifiers, etc.
    """
    # Check if language exists
    language = db.query(Language).filter(Language.id == language_id).first()
    if not language:
        raise HTTPException(status_code=404, detail="Language not found")
    
    # Build query
    query = db.query(UserLanguage).filter(UserLanguage.language_id == language_id)
    
    # Apply filters
    if proficiency is not None:
        query = query.filter(UserLanguage.proficiency_level == proficiency)
    if can_edit is not None:
        query = query.filter(UserLanguage.can_edit == can_edit)
    if can_verify is not None:
        query = query.filter(UserLanguage.can_verify == can_verify)
    
    users = query.all()
    
    return users

