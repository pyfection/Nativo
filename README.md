# Nativo

A web platform dedicated to preserving endangered languages through the collection and preservation of written documents, vocabulary, and spoken audio recordings.

## Mission

Many languages around the world are at risk of disappearing. Nativo provides a digital platform to:
- Record and preserve written documents in endangered languages
- Build vocabulary databases with translations and pronunciations
- Store audio recordings of native speakers
- Make this knowledge accessible for future generations and language learners

## Project Structure

```
nativo/
├── backend/          # FastAPI + SQLAlchemy backend
├── frontend/         # React frontend
└── docker/          # Docker configuration
```

## Technology Stack

### Backend
- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: SQL toolkit and ORM
- **Alembic**: Database migrations
- **UV**: Fast Python package manager

### Frontend
- **React**: UI library
- **TypeScript**: Type-safe JavaScript
- **Vite**: Fast build tool

## Getting Started

### Prerequisites
- Python 3.13+
- Node.js 18+
- UV (Python package manager)

### Backend Setup

```bash
# Navigate to backend
cd backend

# Install dependencies with UV
uv sync

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
uv run alembic upgrade head

# Start development server
uv run uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`
API documentation at `http://localhost:8000/docs`

### Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:5173`

### Docker Setup

```bash
# Build and run both services
docker-compose up --build
```

## Development

### Backend
- API endpoints are in `backend/app/api/v1/endpoints/`
- Database models in `backend/app/models/`
- Pydantic schemas in `backend/app/schemas/`
- Business logic in `backend/app/services/`

### Frontend
- Components organized by feature in `frontend/src/components/`
- Pages in `frontend/src/pages/`
- API services in `frontend/src/services/`
- Custom hooks in `frontend/src/hooks/`

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - See LICENSE file for details

