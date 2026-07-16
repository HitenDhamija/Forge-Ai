# Developer Guide

## Getting Started

### Development Setup

1. **Clone the repository**
```bash
git clone https://github.com/forgeai/forgeai.git
cd forgeai
```

2. **Backend setup**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

3. **Frontend setup**
```bash
cd frontend
npm install
```

4. **Database setup**
```bash
docker-compose up -d postgres redis
alembic upgrade head
```

### Running Locally

```bash
# Terminal 1 - Backend
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

## Project Structure

```
forgeai/
├── backend/
│   ├── app/
│   │   ├── api/v1/        # API endpoints
│   │   ├── core/          # Core business logic
│   │   ├── models/        # SQLAlchemy models
│   │   ├── agents/        # AI agents
│   │   ├── workflows/     # Workflow engine
│   │   ├── memory/        # Semantic memory
│   │   ├── learning/      # Learning engine
│   │   ├── monitoring/    # Monitoring system
│   │   ├── studio/        # Studio backend
│   │   ├── plugins/       # Plugin system
│   │   ├── organizations/ # Organization system
│   │   ├── developer/     # Developer experience
│   │   ├── experience/    # Enterprise experience
│   │   ├── validation/    # Validation suite
│   │   └── infrastructure/# Infrastructure
│   └── tests/
├── frontend/
│   ├── app/               # Next.js pages
│   ├── components/        # React components
│   ├── stores/            # Zustand stores
│   ├── services/          # API services
│   ├── types/             # TypeScript types
│   └── hooks/             # Custom hooks
└── docs/                  # Documentation
```

## Development Workflow

### Creating a Feature

1. Create a branch: `git checkout -b feature/my-feature`
2. Write code following conventions
3. Add tests
4. Run linter: `npm run lint`
5. Run typecheck: `npm run typecheck`
6. Commit with conventional commits
7. Create PR

### Code Conventions

#### Python
- Follow PEP 8
- Use type hints
- Docstrings for public functions
- async/await for I/O operations

#### TypeScript
- Use strict mode
- Prefer interfaces over types
- Use functional components
- Follow React patterns

### Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm run test
```

## API Development

### Creating Endpoints

1. Define schema in `schemas.py`
2. Create route in `api/v1/`
3. Add to router
4. Write tests
5. Update API docs

### Database Changes

1. Create model
2. Generate migration: `alembic revision --autogenerate -m "description"`
3. Review migration
4. Apply: `alembic upgrade head`

## Plugin Development

See [Plugin SDK](./PLUGIN_SDK.md) for details.

## Troubleshooting

### Common Issues

**Database connection refused**
- Ensure PostgreSQL is running
- Check connection string in `.env`

**Ollama not responding**
- Start Ollama: `ollama serve`
- Pull model: `ollama pull qwen2.5`

**Frontend build errors**
- Clear node_modules: `rm -rf node_modules && npm install`
