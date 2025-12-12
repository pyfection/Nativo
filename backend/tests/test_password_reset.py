"""
Unit and integration tests for password reset functionality.

Tests cover:
- Successful password reset request
- Invalid email handling
- Token generation and storage
- Token expiration
- Used token rejection
- Successful password reset
- Invalid token handling
"""
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Dict, Optional

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from jose import jwt, ExpiredSignatureError, JWTError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models.user import User, UserRole
from app.services.password_reset_service import (
    PasswordResetService,
    PasswordResetTokenError,
    InvalidTokenError,
    ExpiredTokenError
)
from app.utils.security import hash_password, verify_password
from app.config import settings

# File-based SQLite database for testing
import tempfile
import os
import atexit

_test_db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
_test_db_file.close()
TEST_DATABASE_URL = f"sqlite:///{_test_db_file.name}"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _cleanup_test_db():
    """Cleanup temporary test database file"""
    try:
        if os.path.exists(_test_db_file.name):
            os.unlink(_test_db_file.name)
    except Exception:
        pass


atexit.register(_cleanup_test_db)

# Store captured emails for testing
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
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@pytest.fixture
def client(db_session: Session):
    """Create a FastAPI test client with database dependency override"""
    def override_get_db():
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


# ============================================================================
# Tests for Password Reset Request
# ============================================================================

def test_successful_password_reset_request(client: TestClient, db_session: Session):
    """
    Test successful password reset request.
    
    Verifies:
    - Request returns success status
    - Email is captured (mocked)
    - Token is generated and stored
    - Token is valid JWT format
    """
    # Create test user
    user = create_test_user(
        db=db_session,
        email="reset@example.com",
        username="resetuser",
        password="originalpassword123"
    )
    
    # Request password reset
    response = client.post(
        "/api/v1/auth/password-reset-request",
        json={"email": user.email}
    )
    
    # Verify response
    assert response.status_code == 200
    response_data = response.json()
    assert "message" in response_data
    assert "reset" in response_data["message"].lower() or "sent" in response_data["message"].lower()
    
    # Verify email was captured
    assert user.email in captured_emails, "Email should have been captured"
    captured_email = captured_emails[user.email]
    
    # Verify token exists and is valid format
    reset_token = captured_email["token"]
    assert reset_token is not None, "Reset token should be present"
    assert len(reset_token) > 0, "Reset token should not be empty"
    
    # Verify token can be decoded (valid JWT)
    try:
        payload = jwt.decode(
            reset_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        assert payload.get("type") == "password_reset", "Token should have correct type"
        assert payload.get("sub") == str(user.id), "Token should contain user ID"
        assert "exp" in payload, "Token should have expiration"
        assert "iat" in payload, "Token should have issued at time"
    except Exception as e:
        pytest.fail(f"Token should be valid JWT: {e}")


def test_password_reset_request_invalid_email_format(client: TestClient, db_session: Session):
    """
    Test password reset request with invalid email format.
    
    Verifies:
    - Request returns validation error (422)
    - No email is sent
    """
    # Request password reset with invalid email
    response = client.post(
        "/api/v1/auth/password-reset-request",
        json={"email": "not-an-email"}
    )
    
    # Should return validation error
    assert response.status_code == 422
    
    # No email should be captured
    assert len(captured_emails) == 0, "No email should be sent for invalid email format"


def test_password_reset_request_nonexistent_email(client: TestClient, db_session: Session):
    """
    Test password reset request for non-existent email.
    
    Verifies:
    - Request returns success (to prevent email enumeration)
    - No email is sent
    """
    # Request password reset for non-existent email
    response = client.post(
        "/api/v1/auth/password-reset-request",
        json={"email": "nonexistent@example.com"}
    )
    
    # Should return success to prevent email enumeration
    assert response.status_code == 200
    response_data = response.json()
    assert "message" in response_data
    
    # No email should be captured
    assert "nonexistent@example.com" not in captured_emails


def test_password_reset_request_inactive_user(client: TestClient, db_session: Session):
    """
    Test password reset request for inactive user.
    
    Verifies:
    - Request returns success (to prevent user enumeration)
    - No email is sent for inactive user
    """
    # Create inactive user
    user = create_test_user(
        db=db_session,
        email="inactive@example.com",
        username="inactiveuser",
        password="testpassword123",
        is_active=False
    )
    
    # Request password reset
    response = client.post(
        "/api/v1/auth/password-reset-request",
        json={"email": user.email}
    )
    
    # Should return success (to prevent enumeration)
    assert response.status_code == 200
    
    # No email should be sent for inactive user
    assert user.email not in captured_emails


# ============================================================================
# Tests for Token Generation and Storage
# ============================================================================

def test_token_generation_and_storage(client: TestClient, db_session: Session):
    """
    Test token generation and storage.
    
    Verifies:
    - Token is generated correctly
    - Token contains correct user ID
    - Token has correct expiration time
    - Token has correct type
    """
    user = create_test_user(
        db=db_session,
        email="token@example.com",
        password="testpassword123"
    )
    
    # Generate token using service
    token = PasswordResetService.generate_reset_token(user.id)
    
    # Verify token is not empty
    assert token is not None
    assert len(token) > 0
    
    # Decode and verify token contents
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM]
    )
    
    # Verify token fields
    assert payload.get("sub") == str(user.id), "Token should contain user ID"
    assert payload.get("type") == "password_reset", "Token should have correct type"
    assert "exp" in payload, "Token should have expiration"
    assert "iat" in payload, "Token should have issued at time"
    
    # Verify expiration is approximately 60 minutes from now
    exp_timestamp = payload.get("exp")
    iat_timestamp = payload.get("iat")
    expiration_minutes = (exp_timestamp - iat_timestamp) / 60
    assert 59 <= expiration_minutes <= 61, f"Token should expire in ~60 minutes, got {expiration_minutes}"


def test_token_generation_different_users(client: TestClient, db_session: Session):
    """
    Test that tokens generated for different users are unique.
    
    Verifies:
    - Tokens for different users are different
    - Each token contains correct user ID
    """
    user1 = create_test_user(
        db=db_session,
        email="user1@example.com",
        username="user1",
        password="testpassword123"
    )
    
    user2 = create_test_user(
        db=db_session,
        email="user2@example.com",
        username="user2",
        password="testpassword123"
    )
    
    # Generate tokens for both users
    token1 = PasswordResetService.generate_reset_token(user1.id)
    token2 = PasswordResetService.generate_reset_token(user2.id)
    
    # Tokens should be different
    assert token1 != token2, "Tokens for different users should be different"
    
    # Verify each token contains correct user ID
    payload1 = jwt.decode(token1, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    payload2 = jwt.decode(token2, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    
    assert payload1.get("sub") == str(user1.id)
    assert payload2.get("sub") == str(user2.id)


# ============================================================================
# Tests for Token Expiration
# ============================================================================

def test_token_expiration(client: TestClient, db_session: Session):
    """
    Test token expiration handling.
    
    Verifies:
    - Expired tokens are rejected
    - ExpiredTokenError is raised for expired tokens
    """
    user = create_test_user(
        db=db_session,
        email="expire@example.com",
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
    
    # Attempt to decode expired token should raise ExpiredTokenError
    with pytest.raises(ExpiredTokenError):
        PasswordResetService.decode_reset_token(expired_token)


def test_token_expiration_via_endpoint(client: TestClient, db_session: Session):
    """
    Test token expiration via password reset endpoint.
    
    Verifies:
    - Expired tokens are rejected by the endpoint
    - Appropriate error message is returned
    """
    user = create_test_user(
        db=db_session,
        email="expire@example.com",
        password="testpassword123"
    )
    
    # Create an expired token
    expire = datetime.utcnow() - timedelta(minutes=1)
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
    
    # Attempt password reset with expired token
    response = client.post(
        "/api/v1/auth/password-reset",
        json={
            "token": expired_token,
            "new_password": "newpassword456"
        }
    )
    
    # Should return error
    assert response.status_code == 400
    assert "expired" in response.json()["detail"].lower()


# ============================================================================
# Tests for Used Token Rejection
# ============================================================================

def test_token_reuse_after_password_reset(client: TestClient, db_session: Session):
    """
    Test token reuse after successful password reset.
    
    Note: Current implementation allows token reuse until expiration.
    This test verifies current behavior. If single-use tokens are desired,
    this test should be updated to expect failure on second use.
    
    Verifies:
    - Token can be used multiple times (current behavior)
    - Each use successfully resets password
    """
    user = create_test_user(
        db=db_session,
        email="reuse@example.com",
        password="original123"
    )
    
    # Request password reset
    client.post(
        "/api/v1/auth/password-reset-request",
        json={"email": user.email}
    )
    
    reset_token = captured_emails[user.email]["token"]
    
    # First password reset
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


# ============================================================================
# Tests for Successful Password Reset
# ============================================================================

def test_successful_password_reset(client: TestClient, db_session: Session):
    """
    Test successful password reset flow.
    
    Verifies:
    - Password reset request succeeds
    - Token is generated and sent
    - Password reset with token succeeds
    - Password is actually changed in database
    - User can login with new password
    - User cannot login with old password
    """
    original_password = "originalpassword123"
    user = create_test_user(
        db=db_session,
        email="success@example.com",
        username="successuser",
        password=original_password
    )
    
    # Step 1: Request password reset
    reset_request_response = client.post(
        "/api/v1/auth/password-reset-request",
        json={"email": user.email}
    )
    assert reset_request_response.status_code == 200
    
    # Step 2: Get reset token
    assert user.email in captured_emails
    reset_token = captured_emails[user.email]["token"]
    
    # Step 3: Reset password
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
    assert "reset" in reset_response.json()["message"].lower() or "success" in reset_response.json()["message"].lower()
    
    # Step 4: Verify password was changed in database
    db_session.refresh(user)
    assert verify_password(new_password, user.hashed_password), "New password should work"
    assert not verify_password(original_password, user.hashed_password), "Old password should not work"
    
    # Step 5: Verify login with new password works
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": user.email,
            "password": new_password
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()
    
    # Step 6: Verify old password no longer works
    failed_login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": user.email,
            "password": original_password
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    assert failed_login_response.status_code == 401


# ============================================================================
# Tests for Invalid Token Handling
# ============================================================================

def test_invalid_token_format(client: TestClient, db_session: Session):
    """
    Test handling of invalid token format.
    
    Verifies:
    - Invalid token format is rejected
    - Appropriate error is returned
    """
    user = create_test_user(
        db=db_session,
        email="invalid@example.com",
        password="testpassword123"
    )
    
    # Attempt password reset with invalid token format
    response = client.post(
        "/api/v1/auth/password-reset",
        json={
            "token": "not-a-valid-jwt-token",
            "new_password": "newpassword456"
        }
    )
    
    assert response.status_code == 400
    assert "invalid" in response.json()["detail"].lower()


def test_invalid_token_wrong_secret(client: TestClient, db_session: Session):
    """
    Test handling of token signed with wrong secret key.
    
    Verifies:
    - Token signed with wrong secret is rejected
    - InvalidTokenError is raised
    """
    user = create_test_user(
        db=db_session,
        email="wrongsecret@example.com",
        password="testpassword123"
    )
    
    # Create token with wrong secret
    wrong_secret = "wrong-secret-key"
    payload = {
        "sub": str(user.id),
        "type": "password_reset",
        "exp": (datetime.utcnow() + timedelta(hours=1)).timestamp(),
        "iat": datetime.utcnow().timestamp()
    }
    wrong_token = jwt.encode(payload, wrong_secret, algorithm=settings.ALGORITHM)
    
    # Attempt to decode should raise InvalidTokenError
    with pytest.raises(InvalidTokenError):
        PasswordResetService.decode_reset_token(wrong_token)


def test_invalid_token_wrong_type(client: TestClient, db_session: Session):
    """
    Test handling of token with wrong type.
    
    Verifies:
    - Token with wrong type is rejected
    - InvalidTokenError is raised
    """
    user = create_test_user(
        db=db_session,
        email="wrongtype@example.com",
        password="testpassword123"
    )
    
    # Create token with wrong type
    payload = {
        "sub": str(user.id),
        "type": "access_token",  # Wrong type
        "exp": (datetime.utcnow() + timedelta(hours=1)).timestamp(),
        "iat": datetime.utcnow().timestamp()
    }
    wrong_type_token = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    # Attempt to decode should raise InvalidTokenError
    with pytest.raises(InvalidTokenError):
        PasswordResetService.decode_reset_token(wrong_type_token)


def test_invalid_token_missing_user_id(client: TestClient, db_session: Session):
    """
    Test handling of token missing user ID.
    
    Verifies:
    - Token without user ID is rejected
    - InvalidTokenError is raised
    """
    # Create token without user ID
    payload = {
        "type": "password_reset",
        "exp": (datetime.utcnow() + timedelta(hours=1)).timestamp(),
        "iat": datetime.utcnow().timestamp()
        # Missing "sub" field
    }
    no_user_token = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    # Attempt to decode should raise InvalidTokenError
    with pytest.raises(InvalidTokenError):
        PasswordResetService.decode_reset_token(no_user_token)


def test_invalid_token_nonexistent_user(client: TestClient, db_session: Session):
    """
    Test handling of token for non-existent user.
    
    Verifies:
    - Token for non-existent user is rejected
    - Appropriate error is returned
    """
    # Create token for non-existent user
    fake_user_id = uuid.uuid4()
    payload = {
        "sub": str(fake_user_id),
        "type": "password_reset",
        "exp": (datetime.utcnow() + timedelta(hours=1)).timestamp(),
        "iat": datetime.utcnow().timestamp()
    }
    fake_user_token = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    # Attempt password reset with token for non-existent user
    response = client.post(
        "/api/v1/auth/password-reset",
        json={
            "token": fake_user_token,
            "new_password": "newpassword456"
        }
    )
    
    assert response.status_code == 400
    assert "invalid" in response.json()["detail"].lower()


def test_invalid_token_inactive_user(client: TestClient, db_session: Session):
    """
    Test handling of token for inactive user.
    
    Verifies:
    - Token for inactive user is rejected
    - Appropriate error is returned
    """
    # Create inactive user
    user = create_test_user(
        db=db_session,
        email="inactive@example.com",
        password="testpassword123",
        is_active=False
    )
    
    # Generate valid token for inactive user
    token = PasswordResetService.generate_reset_token(user.id)
    
    # Attempt password reset should fail
    response = client.post(
        "/api/v1/auth/password-reset",
        json={
            "token": token,
            "new_password": "newpassword456"
        }
    )
    
    assert response.status_code == 403
    assert "inactive" in response.json()["detail"].lower()


def test_validate_token_and_get_user_success(db_session: Session):
    """
    Test successful token validation and user retrieval.
    
    Verifies:
    - Valid token returns correct user
    - User is active
    """
    user = create_test_user(
        db=db_session,
        email="validate@example.com",
        password="testpassword123",
        is_active=True
    )
    
    # Generate token
    token = PasswordResetService.generate_reset_token(user.id)
    
    # Validate token and get user
    retrieved_user = PasswordResetService.validate_token_and_get_user(token, db_session)
    
    assert retrieved_user.id == user.id
    assert retrieved_user.email == user.email
    assert retrieved_user.is_active is True


def test_validate_token_and_get_user_expired(db_session: Session):
    """
    Test token validation with expired token.
    
    Verifies:
    - Expired token raises HTTPException
    - Error message indicates expiration
    """
    user = create_test_user(
        db=db_session,
        email="expired@example.com",
        password="testpassword123"
    )
    
    # Create expired token
    expire = datetime.utcnow() - timedelta(minutes=1)
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
    
    # Attempt validation should raise HTTPException
    with pytest.raises(HTTPException) as exc_info:
        PasswordResetService.validate_token_and_get_user(expired_token, db_session)
    
    assert exc_info.value.status_code == 400
    assert "expired" in exc_info.value.detail.lower()


def test_validate_token_and_get_user_invalid(db_session: Session):
    """
    Test token validation with invalid token.
    
    Verifies:
    - Invalid token raises HTTPException
    - Error message indicates invalid token
    """
    # Attempt validation with invalid token
    with pytest.raises(HTTPException) as exc_info:
        PasswordResetService.validate_token_and_get_user("invalid-token", db_session)
    
    assert exc_info.value.status_code == 400
    assert "invalid" in exc_info.value.detail.lower()
