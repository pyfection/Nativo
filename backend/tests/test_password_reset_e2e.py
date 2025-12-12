"""
End-to-end tests for password reset flow.

Tests the complete password reset workflow:
1. Request password reset
2. Receive email (mocked)
3. Use token to reset password
4. Verify login with new password works
5. Verify old password no longer works
"""
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Dict, Optional

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models.user import User, UserRole
from app.utils.security import hash_password, verify_password


# File-based SQLite database for testing (in-memory is connection-scoped)
import tempfile
import os
import atexit

_test_db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
_test_db_file.close()
TEST_DATABASE_URL = f"sqlite:///{_test_db_file.name}"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Cleanup temp file on exit
def _cleanup_test_db():
    try:
        if os.path.exists(_test_db_file.name):
            os.unlink(_test_db_file.name)
    except Exception:
        pass

atexit.register(_cleanup_test_db)


# Store captured emails
captured_emails: Dict[str, Dict[str, str]] = {}


def mock_send_password_reset_email(email: str, reset_token: str, reset_url: Optional[str] = None) -> bool:
    """
    Mock email service that captures emails instead of sending them.
    
    Args:
        email: Recipient email address
        reset_token: Password reset token
        reset_url: Optional reset URL
        
    Returns:
        True to simulate successful email sending
    """
    captured_emails[email] = {
        "token": reset_token,
        "reset_url": reset_url or f"http://localhost:5173/password-reset?token={reset_token}"
    }
    return True


@pytest.fixture(autouse=True)
def setup_database():
    """Create and drop database tables for each test"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    # Clear captured emails between tests
    captured_emails.clear()


@pytest.fixture
def db_session() -> Session:
    """Create a database session for testing"""
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
        session.commit()  # Commit any pending changes
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@pytest.fixture
def client(db_session: Session):
    """Create a FastAPI test client with database dependency override"""
    def override_get_db():
        # Create a new session from the same engine for each request
        # This ensures we use the same in-memory database
        session = TestingSessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Mock the email service to capture emails
    async def mock_email_async(email: str, reset_token: str, reset_url: Optional[str] = None) -> bool:
        """Async wrapper for email mock"""
        return mock_send_password_reset_email(email, reset_token, reset_url)
    
    with patch('app.services.email_service.email_service.send_password_reset_email', side_effect=mock_email_async):
        with TestClient(app) as test_client:
            yield test_client
    
    app.dependency_overrides.clear()


def create_test_user(
    db: Session,
    email: str = "test@example.com",
    username: str = "testuser",
    password: str = "testpassword123",
    role: UserRole = UserRole.PUBLIC,
    is_active: bool = True
) -> User:
    """
    Helper function to create a test user.
    
    Args:
        db: Database session
        email: User email
        username: Username
        password: Plain text password
        role: User role
        is_active: Whether user is active
        
    Returns:
        Created User object
    """
    user = User(
        id=uuid.uuid4(),
        email=email,
        username=username,
        hashed_password=hash_password(password),
        role=role,
        is_active=is_active,
        is_superuser=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_password_reset_complete_flow(client: TestClient, db_session: Session):
    """
    Test the complete password reset flow end-to-end.
    
    This test verifies:
    1. User can request password reset
    2. Email is sent (mocked) with reset token
    3. User can reset password using token
    4. User can login with new password
    5. Old password no longer works
    """
    # Step 1: Create a test user
    original_password = "originalpassword123"
    user = create_test_user(
        db=db_session,
        email="reset@example.com",
        username="resetuser",
        password=original_password
    )
    
    # Step 2: Request password reset
    reset_request_response = client.post(
        "/api/v1/auth/password-reset-request",
        json={"email": user.email}
    )
    
    assert reset_request_response.status_code == 200
    assert "message" in reset_request_response.json()
    assert "reset" in reset_request_response.json()["message"].lower()
    
    # Step 3: Verify email was captured (mocked)
    assert user.email in captured_emails, "Email should have been captured"
    captured_email = captured_emails[user.email]
    reset_token = captured_email["token"]
    assert reset_token is not None, "Reset token should be present"
    assert len(reset_token) > 0, "Reset token should not be empty"
    
    # Step 4: Reset password using token
    new_password = "newpassword456"
    reset_response = client.post(
        "/api/v1/auth/password-reset",
        json={
            "token": reset_token,
            "new_password": new_password
        }
    )
    
    assert reset_response.status_code == 200
    assert "message" in reset_response.json()
    assert "reset" in reset_response.json()["message"].lower()
    
    # Step 5: Verify password was actually changed in database
    db_session.refresh(user)
    assert verify_password(new_password, user.hashed_password), "New password should work"
    assert not verify_password(original_password, user.hashed_password), "Old password should not work"
    
    # Step 6: Verify login with new password works
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": user.email,  # Can use email or username
            "password": new_password
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()
    assert login_response.json()["token_type"] == "bearer"
    
    # Step 7: Verify old password no longer works
    failed_login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": user.email,
            "password": original_password
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    assert failed_login_response.status_code == 401
    assert "incorrect" in failed_login_response.json()["detail"].lower()


def test_password_reset_request_for_nonexistent_email(client: TestClient, db_session: Session):
    """
    Test that password reset request returns success even for non-existent emails
    (to prevent email enumeration attacks).
    """
    response = client.post(
        "/api/v1/auth/password-reset-request",
        json={"email": "nonexistent@example.com"}
    )
    
    # Should return success to prevent email enumeration
    assert response.status_code == 200
    assert "message" in response.json()
    
    # No email should be captured for non-existent user
    assert "nonexistent@example.com" not in captured_emails


def test_password_reset_with_invalid_token(client: TestClient, db_session: Session):
    """Test that password reset fails with invalid token"""
    user = create_test_user(
        db=db_session,
        email="test@example.com",
        password="testpassword123"
    )
    
    response = client.post(
        "/api/v1/auth/password-reset",
        json={
            "token": "invalid_token_12345",
            "new_password": "newpassword456"
        }
    )
    
    assert response.status_code == 400
    assert "invalid" in response.json()["detail"].lower() or "expired" in response.json()["detail"].lower()


def test_password_reset_with_expired_token(client: TestClient, db_session: Session):
    """
    Test that password reset fails with expired token.
    
    Note: This test uses a token that's manually expired by manipulating
    the token expiration time in the password reset service.
    """
    from datetime import datetime, timedelta
    from jose import jwt
    from app.config import settings
    
    user = create_test_user(
        db=db_session,
        email="test@example.com",
        password="testpassword123"
    )
    
    # Create an expired token manually
    expire = datetime.utcnow() - timedelta(minutes=1)  # Expired 1 minute ago
    expired_payload = {
        "sub": str(user.id),
        "type": "password_reset",
        "exp": expire.timestamp(),
        "iat": (datetime.utcnow() - timedelta(hours=2)).timestamp()
    }
    expired_token = jwt.encode(
        expired_payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    response = client.post(
        "/api/v1/auth/password-reset",
        json={
            "token": expired_token,
            "new_password": "newpassword456"
        }
    )
    
    assert response.status_code == 400
    assert "expired" in response.json()["detail"].lower()


def test_password_reset_with_weak_password(client: TestClient, db_session: Session):
    """Test that password reset fails with weak password"""
    user = create_test_user(
        db=db_session,
        email="test@example.com",
        password="testpassword123"
    )
    
    # Request reset
    client.post(
        "/api/v1/auth/password-reset-request",
        json={"email": user.email}
    )
    
    # Get token
    assert user.email in captured_emails
    reset_token = captured_emails[user.email]["token"]
    
    # Try to reset with weak password
    response = client.post(
        "/api/v1/auth/password-reset",
        json={
            "token": reset_token,
            "new_password": "short"  # Too short
        }
    )
    
    assert response.status_code == 422  # Validation error


def test_password_reset_for_inactive_user(client: TestClient, db_session: Session):
    """
    Test that password reset request doesn't send email for inactive users,
    but still returns success message (to prevent user enumeration).
    """
    user = create_test_user(
        db=db_session,
        email="inactive@example.com",
        password="testpassword123",
        is_active=False
    )
    
    response = client.post(
        "/api/v1/auth/password-reset-request",
        json={"email": user.email}
    )
    
    # Should return success (to prevent enumeration)
    assert response.status_code == 200
    
    # But no email should be sent for inactive user
    assert user.email not in captured_emails


def test_password_reset_token_single_use(client: TestClient, db_session: Session):
    """
    Test that password reset token can be used multiple times (if not expired).
    
    Note: Current implementation allows token reuse until expiration.
    This test verifies current behavior. If single-use tokens are desired,
    this test should be updated to expect failure on second use.
    """
    user = create_test_user(
        db=db_session,
        email="test@example.com",
        password="original123"
    )
    
    # Request reset
    client.post(
        "/api/v1/auth/password-reset-request",
        json={"email": user.email}
    )
    
    reset_token = captured_emails[user.email]["token"]
    
    # First reset
    response1 = client.post(
        "/api/v1/auth/password-reset",
        json={
            "token": reset_token,
            "new_password": "newpassword1"
        }
    )
    assert response1.status_code == 200
    
    # Verify password changed
    db_session.refresh(user)
    assert verify_password("newpassword1", user.hashed_password)
    
    # Token can still be used (current implementation allows reuse)
    # If single-use tokens are implemented, this should fail
    response2 = client.post(
        "/api/v1/auth/password-reset",
        json={
            "token": reset_token,
            "new_password": "newpassword2"
        }
    )
    # Current implementation allows reuse, so this succeeds
    # If single-use is desired, change this assertion to expect 400
    assert response2.status_code == 200
    
    # Verify password changed again
    db_session.refresh(user)
    assert verify_password("newpassword2", user.hashed_password)


def test_password_reset_login_with_username(client: TestClient, db_session: Session):
    """Test that login works with username after password reset"""
    original_password = "original123"
    user = create_test_user(
        db=db_session,
        email="test@example.com",
        username="testuser",
        password=original_password
    )
    
    # Request reset
    client.post(
        "/api/v1/auth/password-reset-request",
        json={"email": user.email}
    )
    
    reset_token = captured_emails[user.email]["token"]
    new_password = "newpassword123"
    
    # Reset password
    client.post(
        "/api/v1/auth/password-reset",
        json={
            "token": reset_token,
            "new_password": new_password
        }
    )
    
    # Login with username (not email)
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": user.username,
            "password": new_password
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()
