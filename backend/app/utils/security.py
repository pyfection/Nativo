"""
Security utilities for password hashing and verification.
"""
import logging
import bcrypt
import hashlib

logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    """
    Hash a plain password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password
        
    Raises:
        ValueError: If password hashing fails
    """
    try:
        # Convert to bytes and truncate to 72 bytes if necessary
        password_bytes = password.encode('utf-8')[:72]
        
        # Generate salt and hash
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        
        # Return as string
        return hashed.decode('utf-8')
    except Exception as e:
        logger.error(
            f"Failed to hash password",
            extra={"error": str(e)},
            exc_info=True
        )
        raise ValueError("Failed to process password. Please try again.") from e


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against
        
    Returns:
        True if password matches, False otherwise
    """
    # Convert to bytes
    password_bytes = plain_password.encode('utf-8')[:72]
    hashed_bytes = hashed_password.encode('utf-8')
    
    # Verify
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def hash_token(token: str) -> str:
    """
    Hash a token for storage in the database.
    
    Uses SHA-256 to create a deterministic hash of the token.
    This allows us to check if a token has been used without
    storing the actual token value.
    
    Args:
        token: Token string to hash
        
    Returns:
        SHA-256 hash of the token as a hexadecimal string
    """
    return hashlib.sha256(token.encode('utf-8')).hexdigest()

