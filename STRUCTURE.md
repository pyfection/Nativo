# Nativo Project Structure

This document outlines the complete folder structure of the Nativo project.

## Root Level
```
nativo/
├── backend/              # FastAPI backend application
├── frontend/             # React frontend application
├── docker/              # Docker configuration files
├── .gitignore           # Git ignore rules
├── pyproject.toml       # Python project configuration (UV)
├── README.md            # Project documentation
└── STRUCTURE.md         # This file
```

## Backend Structure (`backend/`)
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application entry point
│   ├── config.py                  # Configuration settings
│   ├── database.py                # Database connection and session
│   │
│   ├── api/                       # API layer
│   │   ├── __init__.py
│   │   ├── deps.py                # Shared dependencies
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py          # API v1 router
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── languages.py   # Language endpoints
│   │           ├── documents.py   # Document endpoints
│   │           ├── words.py       # Word endpoints
│   │           ├── audio.py       # Audio endpoints
│   │           └── users.py       # User/auth endpoints
│   │
│   ├── models/                    # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── language.py
│   │   ├── document.py
│   │   ├── word.py
│   │   ├── audio.py
│   │   └── user.py
│   │
│   ├── schemas/                   # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── language.py
│   │   ├── document.py
│   │   ├── word.py
│   │   ├── audio.py
│   │   └── user.py
│   │
│   ├── services/                  # Business logic layer
│   │   ├── __init__.py
│   │   ├── language_service.py
│   │   ├── document_service.py
│   │   ├── audio_service.py
│   │   └── auth_service.py
│   │
│   └── utils/                     # Utility functions
│       ├── __init__.py
│       ├── audio_processing.py
│       └── file_storage.py
│
├── alembic/                       # Database migrations
│   ├── versions/
│   │   └── .gitkeep
│   └── env.py
│
├── tests/                         # Test suite
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_languages.py
│   ├── test_documents.py
│   ├── test_audio.py
│   └── test_words.py
│
├── uploads/                       # File storage
│   ├── documents/
│   │   └── .gitkeep
│   └── audio/
│       └── .gitkeep
│
├── .env.example                   # Example environment variables
└── alembic.ini                    # Alembic configuration
```

## Frontend Structure (`frontend/`)
```
frontend/
├── public/
│   ├── index.html
│   └── favicon.ico
│
├── src/
│   ├── components/
│   │   ├── common/                # Reusable components
│   │   │   ├── Button.tsx
│   │   │   ├── Modal.tsx
│   │   │   ├── AudioPlayer.tsx
│   │   │   └── FileUpload.tsx
│   │   │
│   │   ├── languages/             # Language components
│   │   │   ├── LanguageList.tsx
│   │   │   ├── LanguageCard.tsx
│   │   │   └── LanguageForm.tsx
│   │   │
│   │   ├── documents/             # Document components
│   │   │   ├── DocumentList.tsx
│   │   │   ├── DocumentViewer.tsx
│   │   │   └── DocumentUpload.tsx
│   │   │
│   │   ├── words/                 # Word components
│   │   │   ├── WordList.tsx
│   │   │   ├── WordCard.tsx
│   │   │   └── WordForm.tsx
│   │   │
│   │   └── audio/                 # Audio components
│   │       ├── AudioRecorder.tsx
│   │       ├── AudioList.tsx
│   │       └── AudioUpload.tsx
│   │
│   ├── pages/                     # Page components
│   │   ├── Home.tsx
│   │   ├── Languages.tsx
│   │   ├── LanguageDetail.tsx
│   │   ├── Documents.tsx
│   │   ├── Words.tsx
│   │   └── Login.tsx
│   │
│   ├── services/                  # API service layer
│   │   ├── api.ts                 # Base API configuration
│   │   ├── languageService.ts
│   │   ├── documentService.ts
│   │   ├── wordService.ts
│   │   └── audioService.ts
│   │
│   ├── hooks/                     # Custom React hooks
│   │   ├── useLanguages.ts
│   │   ├── useDocuments.ts
│   │   ├── useWords.ts
│   │   └── useAudio.ts
│   │
│   ├── contexts/                  # React contexts
│   │   ├── AuthContext.tsx
│   │   └── ThemeContext.tsx
│   │
│   ├── types/                     # TypeScript type definitions
│   │   ├── language.ts
│   │   ├── document.ts
│   │   ├── word.ts
│   │   └── audio.ts
│   │
│   ├── utils/                     # Utility functions
│   │   ├── formatters.ts
│   │   └── validators.ts
│   │
│   ├── App.tsx                    # Main App component
│   ├── index.tsx                  # Entry point
│   └── index.css                  # Global styles
│
├── package.json                   # Node.js dependencies
├── tsconfig.json                  # TypeScript config
├── tsconfig.node.json             # Node TypeScript config
├── vite.config.ts                 # Vite configuration
└── .env.example                   # Example environment variables
```

## Docker Structure (`docker/`)
```
docker/
├── docker-compose.yml             # Docker Compose configuration
├── Dockerfile.backend             # Backend container
└── Dockerfile.frontend            # Frontend container
```

## Key Design Principles

### Backend
1. **Layered Architecture**: Clear separation between API, business logic, and data layers
2. **API Versioning**: Endpoints organized under `/api/v1/` for future compatibility
3. **Service Layer**: Business logic isolated in services for reusability and testing
4. **Type Safety**: Pydantic schemas for request/response validation

### Frontend
1. **Component-Based**: Features organized by domain (languages, documents, words, audio)
2. **Type Safety**: Full TypeScript coverage with type definitions
3. **Separation of Concerns**: API logic in services, state in hooks, UI in components
4. **Context API**: Global state management with React Context

### File Organization
- **Backend**: Python modules follow standard naming conventions
- **Frontend**: React components use PascalCase, utilities use camelCase
- **Configuration**: All config files at appropriate root levels
- **Tests**: Mirror source structure for easy navigation

