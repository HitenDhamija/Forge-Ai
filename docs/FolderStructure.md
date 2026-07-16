# ForgeAI Folder Structure

## Root Directory

```
forge-ai/
├── .github/                    # GitHub configuration
│   └── workflows/              # CI/CD pipelines
│       ├── ci.yml              # Main CI pipeline
│       └── docker.yml          # Docker build workflow
│
├── app/                        # Backend application (FastAPI)
│   ├── __init__.py
│   ├── main.py                 # Application entry point
│   ├── config.py               # Configuration management
│   ├── dependencies.py         # Dependency injection
│   │
│   ├── api/                    # API Layer
│   │   ├── __init__.py
│   │   ├── router.py           # Main API router
│   │   └── v1/                 # API version 1
│   │       ├── __init__.py
│   │       ├── endpoints/      # API endpoints
│   │       │   ├── __init__.py
│   │       │   ├── health.py
│   │       │   ├── auth.py
│   │       │   ├── users.py
│   │       │   └── tasks.py
│   │       └── schemas/        # Request/Response schemas
│   │           ├── __init__.py
│   │           ├── base.py
│   │           ├── auth.py
│   │           ├── users.py
│   │           └── tasks.py
│   │
│   ├── domain/                 # Domain Layer
│   │   ├── __init__.py
│   │   ├── entities/           # Business entities
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   └── task.py
│   │   ├── value_objects/      # Immutable value objects
│   │   │   ├── __init__.py
│   │   │   ├── email.py
│   │   │   └── password.py
│   │   └── events/             # Domain events
│   │       ├── __init__.py
│   │       └── user_events.py
│   │
│   ├── services/               # Application/Service Layer
│   │   ├── __init__.py
│   │   ├── base.py             # Base service class
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   └── task_service.py
│   │
│   ├── infrastructure/         # Infrastructure Layer
│   │   ├── __init__.py
│   │   ├── database/           # Database configuration
│   │   │   ├── __init__.py
│   │   │   ├── session.py      # Database session
│   │   │   ├── base.py         # SQLAlchemy base
│   │   │   └── models/         # Database models
│   │   │       ├── __init__.py
│   │   │       ├── user.py
│   │   │       └── task.py
│   │   ├── repositories/       # Repository implementations
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── user_repository.py
│   │   │   └── task_repository.py
│   │   ├── cache/              # Cache implementation
│   │   │   ├── __init__.py
│   │   │   └── redis_cache.py
│   │   └── external/           # External service integrations
│   │       ├── __init__.py
│   │       └── ai_providers.py
│   │
│   └── utils/                  # Utility functions
│       ├── __init__.py
│       ├── security.py         # Password hashing, JWT
│       ├── exceptions.py       # Custom exceptions
│       └── logging.py          # Logging configuration
│
├── docker/                     # Docker configuration
│   ├── Dockerfile.backend      # Backend container
│   ├── Dockerfile.frontend     # Frontend container
│   ├── docker-compose.yml      # Production compose
│   ├── docker-compose.dev.yml  # Development compose
│   └── .env.example            # Docker environment
│
├── scripts/                    # Utility scripts
│   ├── setup.sh                # Development setup
│   ├── dev.sh                  # Start dev environment
│   └── stop.sh                 # Stop dev environment
│
├── tests/                      # Test suite
│   ├── conftest.py             # Root test configuration
│   ├── backend/                # Backend tests
│   │   ├── __init__.py
│   │   ├── test_health.py
│   │   ├── test_auth.py
│   │   └── test_users.py
│   └── frontend/               # Frontend tests
│       └── __init__.py
│
├── docs/                       # Documentation
│   ├── Architecture.md
│   ├── FolderStructure.md
│   ├── GettingStarted.md
│   ├── DeveloperGuide.md
│   ├── CodingStandards.md
│   └── Contributing.md
│
├── alembic/                    # Database migrations
│   ├── versions/               # Migration files
│   ├── env.py
│   └── script.py.mako
│
├── frontend/                   # Frontend application (Next.js)
│   ├── public/                 # Static assets
│   ├── src/
│   │   ├── app/                # App router pages
│   │   ├── components/         # React components
│   │   ├── hooks/              # Custom hooks
│   │   ├── lib/                # Utility libraries
│   │   ├── stores/             # State management
│   │   └── types/              # TypeScript types
│   ├── next.config.js
│   ├── tailwind.config.js
│   └── tsconfig.json
│
├── .env.example                # Root environment example
├── .gitignore                  # Git ignore rules
├── pyproject.toml              # Python project configuration
├── poetry.lock                 # Python dependency lock
├── package.json                # Node.js dependencies
├── package-lock.json           # Node.js dependency lock
├── tsconfig.json               # TypeScript configuration
├── README.md                   # Project documentation
└── LICENSE                     # MIT License
```

## Key Files Explained

### Backend Core

| File | Purpose |
|------|---------|
| `app/main.py` | FastAPI application instance, middleware setup, startup/shutdown events |
| `app/config.py` | Pydantic Settings for environment variable management |
| `app/dependencies.py` | FastAPI dependency injection (db session, current user, etc.) |

### API Layer

| Directory | Purpose |
|-----------|---------|
| `app/api/v1/endpoints/` | Route handlers organized by resource |
| `app/api/v1/schemas/` | Pydantic models for request/response validation |
| `app/api/router.py` | Main router aggregating all versioned routers |

### Domain Layer

| Directory | Purpose |
|-----------|---------|
| `app/domain/entities/` | Core business objects (User, Task, etc.) |
| `app/domain/value_objects/` | Immutable objects (Email, Password, etc.) |
| `app/domain/events/` | Domain events for decoupled communication |

### Service Layer

| File | Purpose |
|------|---------|
| `app/services/base.py` | Base service with common functionality |
| `app/services/*_service.py` | Business logic organized by domain |

### Infrastructure Layer

| Directory | Purpose |
|-----------|---------|
| `app/infrastructure/database/` | SQLAlchemy configuration and models |
| `app/infrastructure/repositories/` | Data access implementations |
| `app/infrastructure/cache/` | Redis cache implementation |
| `app/infrastructure/external/` | Third-party API integrations |

### Testing

| File | Purpose |
|------|---------|
| `tests/conftest.py` | Pytest fixtures shared across tests |
| `tests/backend/test_*.py` | Backend unit and integration tests |
| `tests/frontend/` | Frontend component and E2E tests |

### Configuration

| File | Purpose |
|------|---------|
| `pyproject.toml` | Python project metadata and tool configuration |
| `docker-compose.yml` | Production Docker orchestration |
| `docker-compose.dev.yml` | Development Docker with hot reload |
| `.github/workflows/ci.yml` | Automated testing and deployment |

## Naming Conventions

- **Files**: `snake_case.py` for Python, `camelCase.ts` for TypeScript
- **Directories**: `snake_case` for Python, `camelCase` for TypeScript
- **Classes**: `PascalCase` (e.g., `UserService`, `UserRepository`)
- **Functions**: `snake_case` (e.g., `get_user_by_id`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_PAGE_SIZE`)
- **API Endpoints**: `kebab-case` (e.g., `/api/v1/user-profiles`)

---

*This structure follows Clean Architecture principles and can evolve with the project.*
