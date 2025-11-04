#!/usr/bin/env python3
"""
Test script to validate all imports work correctly.
This mimics the imports that happen when the FastAPI app starts.
"""

print("Testing imports...")

try:
    print("1. Importing FastAPI...")
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from starlette.middleware.sessions import SessionMiddleware
    print("   ✓ FastAPI imports successful")
except Exception as e:
    print(f"   ✗ FastAPI imports failed: {e}")
    exit(1)

try:
    print("2. Importing config...")
    from app.config import settings
    print("   ✓ Config imports successful")
except Exception as e:
    print(f"   ✗ Config imports failed: {e}")
    exit(1)

try:
    print("3. Importing API router...")
    from app.api.v1.router import router as api_v1_router
    print("   ✓ API router imports successful")
except Exception as e:
    print(f"   ✗ API router imports failed: {e}")
    exit(1)

try:
    print("4. Importing admin...")
    from app.admin import create_admin
    print("   ✓ Admin imports successful")
except Exception as e:
    print(f"   ✗ Admin imports failed: {e}")
    exit(1)

try:
    print("5. Importing all models...")
    from app.models import (
        User, Language, Audio, Document, Text, Location, Image, Tag, Word
    )
    print("   ✓ Models imports successful")
except Exception as e:
    print(f"   ✗ Models imports failed: {e}")
    exit(1)

try:
    print("6. Importing all schemas...")
    from app.schemas import (
        UserBase, LanguageBase, AudioBase, DocumentBase,
        WordBase, LocationBase, TagBase, ImageBase
    )
    print("   ✓ Schemas imports successful")
except Exception as e:
    print(f"   ✗ Schemas imports failed: {e}")
    exit(1)

print("\n✓ All imports successful!")
print("The application should start without import errors.")
