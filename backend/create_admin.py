#!/usr/bin/env python3
"""
Script to create an admin user for the Nativo platform.

Usage:
    uv run python create_admin.py
"""
from app.database import SessionLocal
from app.models.user import User, UserRole
from app.utils.security import hash_password
import uuid


def create_admin_user(
    username: str = "admin",
    email: str = "admin@nativo.local",
    password: str = "admin123",
    is_superuser: bool = True,
):
    """
    Create an admin user in the database.

    Args:
        username: Username for the admin account
        email: Email for the admin account
        password: Password for the admin account
        is_superuser: Whether the user should be a superuser
    """
    db = SessionLocal()
    try:
        # Check if user already exists
        existing_user = (
            db.query(User)
            .filter((User.username == username) | (User.email == email))
            .first()
        )

        if existing_user:
            print(
                f"❌ User already exists: {existing_user.username} ({existing_user.email})"
            )
            print(
                f"   Role: {existing_user.role}, Superuser: {existing_user.is_superuser}"
            )
            return

        # Create new admin user
        admin_user = User(
            id=uuid.uuid4(),
            username=username,
            email=email,
            hashed_password=hash_password(password),
            role=UserRole.ADMIN,
            is_superuser=is_superuser,
            is_active=True,
        )

        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        print("✅ Admin user created successfully!")
        print(f"   Username: {admin_user.username}")
        print(f"   Email: {admin_user.email}")
        print(f"   Role: {admin_user.role}")
        print(f"   Superuser: {admin_user.is_superuser}")
        print(f"\n🔑 Login credentials:")
        print(f"   Username/Email: {username} or {email}")
        print(f"   Password: {password}")
        print(f"\n🌐 Admin URL: http://localhost:8000/admin")

    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Nativo Admin User Creation Script")
    print("=" * 60)
    print()

    # You can customize these values
    create_admin_user(
        username="admin",
        email="admin@nativo.local",
        password="admin123",  # Change this in production!
        is_superuser=True,
    )

    print()
    print("⚠️  SECURITY WARNING:")
    print("   Please change the default password in production!")
    print("=" * 60)
