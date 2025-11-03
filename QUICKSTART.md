# Nativo Quick Start Guide

This guide will help you get the Nativo platform up and running quickly.

## Prerequisites

- Python 3.13 or higher
- Node.js 18 or higher
- UV (Python package manager): `curl -LsSf https://astral.sh/uv/install.sh | sh`

## Backend Setup

### 1. Install Dependencies

```bash
cd backend
uv sync
```

This will:
- Create a virtual environment (if it doesn't exist)
- Install all dependencies from `pyproject.toml`
- Install development dependencies

### 2. Configure Environment

```bash
# Create .env file from example
cp .env.example .env

# Edit .env with your settings (optional for local development)
# The defaults work fine for local SQLite setup
```

### 3. Initialize Database

```bash
# Run database migrations
uv run alembic upgrade head
```

### 4. Start Backend Server

```bash
# Run the development server
uv run uvicorn app.main:app --reload
```

The API will be available at:
- API: `http://localhost:8000`
- Interactive docs (Swagger): `http://localhost:8000/docs`
- Alternative docs (ReDoc): `http://localhost:8000/redoc`
- Admin interface: `http://localhost:8000/admin`

## Frontend Setup

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment

```bash
# Create .env file from example
cp .env.example .env

# The defaults should work fine for local development
```

### 3. Start Frontend Server

```bash
npm run dev
```

The frontend will be available at: `http://localhost:5173`

## Docker Setup (Alternative)

If you prefer using Docker:

```bash
# From project root
cd docker
docker-compose up --build
```

This will start:
- Backend API on `http://localhost:8000`
- Frontend on `http://localhost:5173`
- PostgreSQL database on `localhost:5432`

## Admin Interface

Nativo includes a web-based admin interface for managing all aspects of the platform.

### Accessing the Admin

1. Navigate to `http://localhost:8000/admin`
2. Login with an admin user account (requires `is_superuser=True` or `role=ADMIN`)

### Features

- Full CRUD operations for all models (Users, Languages, Words, Documents, Audio, etc.)
- Search and filter capabilities
- Bulk operations
- Data export functionality

See `backend/ADMIN_GUIDE.md` for detailed documentation.

## Development Workflow

### Backend Development

1. **Add new endpoint**: Create in `backend/app/api/v1/endpoints/`
2. **Add database model**: Create in `backend/app/models/`
3. **Add schema**: Create in `backend/app/schemas/`
4. **Add business logic**: Create in `backend/app/services/`
5. **Create migration**: `uv run alembic revision --autogenerate -m "description"`
6. **Run tests**: `uv run pytest`

### Frontend Development

1. **Add new page**: Create in `frontend/src/pages/`
2. **Add components**: Create in `frontend/src/components/[feature]/`
3. **Add API service**: Update `frontend/src/services/`
4. **Add types**: Define in `frontend/src/types/`
5. **Build**: `npm run build`

## Testing

### Backend Tests
```bash
cd backend
uv run pytest
uv run pytest --cov=app  # With coverage
```

### Frontend Tests
```bash
cd frontend
npm run test  # Once test scripts are configured
```

## Common Commands

### Backend
```bash
# Format code
uv run ruff format .

# Lint code
uv run ruff check .

# Create new migration
uv run alembic revision --autogenerate -m "add user table"

# Upgrade database
uv run alembic upgrade head

# Downgrade database
uv run alembic downgrade -1
```

### Frontend
```bash
# Development
npm run dev

# Production build
npm run build

# Preview production build
npm run preview

# Lint
npm run lint
```

## Project Structure Overview

```
nativo/
├── backend/          # FastAPI backend (Python)
│   ├── app/         # Application code
│   ├── alembic/     # Database migrations
│   └── tests/       # Test suite
│
├── frontend/        # React frontend (TypeScript)
│   ├── src/         # Source code
│   └── public/      # Static assets
│
└── docker/          # Docker configuration
```

## Next Steps

1. **Define your data models** in `backend/app/models/`
2. **Create Pydantic schemas** in `backend/app/schemas/`
3. **Implement API endpoints** in `backend/app/api/v1/endpoints/`
4. **Build UI components** in `frontend/src/components/`
5. **Create pages** in `frontend/src/pages/`

## Troubleshooting

### Backend won't start
- Check if port 8000 is already in use
- Verify Python version: `python --version`
- Ensure UV is installed: `uv --version`

### Frontend won't start
- Check if port 5173 is already in use
- Verify Node.js version: `node --version`
- Clear node_modules and reinstall: `rm -rf node_modules && npm install`

### Database issues
- Delete `nativo.db` and run `uv run alembic upgrade head` again
- Check DATABASE_URL in `.env`

## Resources

- FastAPI documentation: https://fastapi.tiangolo.com/
- SQLAlchemy documentation: https://docs.sqlalchemy.org/
- React documentation: https://react.dev/
- Vite documentation: https://vitejs.dev/
- UV documentation: https://github.com/astral-sh/uv

