# ForgeAI Developer Guide

## Architecture Overview

ForgeAI follows Clean Architecture principles. Before making changes, familiarize yourself with the [Architecture Documentation](Architecture.md).

### Key Principles

1. **Separation of Concerns**: Each layer has a distinct responsibility
2. **Dependency Rule**: Dependencies point inward (domain has no external dependencies)
3. **Interface Segregation**: Use abstract interfaces for external integrations
4. **Single Responsibility**: Each module does one thing well

## Adding New Modules

### 1. Create Domain Entities

```python
# app/domain/entities/new_module.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class NewEntity:
    """Domain entity for new module."""
    id: Optional[int] = None
    name: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def validate(self) -> bool:
        """Validate entity business rules."""
        return len(self.name) > 0
```

### 2. Create Repository Interface

```python
# app/domain/repositories/new_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.new_module import NewEntity

class NewRepository(ABC):
    """Abstract repository interface."""

    @abstractmethod
    async def get_by_id(self, id: int) -> Optional[NewEntity]:
        pass

    @abstractmethod
    async def create(self, entity: NewEntity) -> NewEntity:
        pass

    @abstractmethod
    async def list_all(self) -> List[NewEntity]:
        pass
```

### 3. Create Database Model

```python
# app/infrastructure/database/models/new_model.py
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.infrastructure.database.base import Base

class NewModel(Base):
    __tablename__ = "new_table"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

### 4. Create Repository Implementation

```python
# app/infrastructure/repositories/new_repository_impl.py
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.new_module import NewEntity
from app.domain.repositories.new_repository import NewRepository
from app.infrastructure.database.models.new_model import NewModel

class NewRepositoryImpl(NewRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: int) -> Optional[NewEntity]:
        result = await self.session.execute(
            select(NewModel).where(NewModel.id == id)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def create(self, entity: NewEntity) -> NewEntity:
        model = NewModel(name=entity.name)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return self._to_domain(model)

    def _to_domain(self, model: NewModel) -> NewEntity:
        return NewEntity(
            id=model.id,
            name=model.name,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
```

### 5. Create Service

```python
# app/services/new_service.py
from typing import List, Optional
from app.domain.entities.new_module import NewEntity
from app.domain.repositories.new_repository import NewRepository
from app.services.base import BaseService

class NewService(BaseService):
    def __init__(self, repository: NewRepository):
        self.repository = repository

    async def get_entity(self, id: int) -> Optional[NewEntity]:
        return await self.repository.get_by_id(id)

    async def create_entity(self, name: str) -> NewEntity:
        entity = NewEntity(name=name)
        if not entity.validate():
            raise ValueError("Invalid entity data")
        return await self.repository.create(entity)
```

### 6. Create API Endpoints

```python
# app/api/v1/endpoints/new_module.py
from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_new_service
from app.api.v1.schemas.new_module import NewCreate, NewResponse
from app.services.new_service import NewService

router = APIRouter()

@router.post("/", response_model=NewResponse)
async def create_entity(
    data: NewCreate,
    service: NewService = Depends(get_new_service),
):
    try:
        return await service.create_entity(name=data.name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{id}", response_model=NewResponse)
async def get_entity(
    id: int,
    service: NewService = Depends(get_new_service),
):
    entity = await service.get_entity(id)
    if not entity:
        raise HTTPException(status_code=404, detail="Not found")
    return entity
```

### 7. Create Schemas

```python
# app/api/v1/schemas/new_module.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class NewCreate(BaseModel):
    name: str

class NewResponse(BaseModel):
    id: int
    name: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
```

### 8. Register Router

```python
# app/api/v1/__init__.py
from fastapi import APIRouter
from app.api.v1.endpoints import health, auth, users, new_module

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(new_module.router, prefix="/new-module", tags=["new-module"])
```

## Adding New API Endpoints

### Standard Endpoint Pattern

```python
@router.get("/items", response_model=List[ItemResponse])
async def list_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: ItemService = Depends(get_item_service),
    current_user: User = Depends(get_current_user),
):
    """List items with pagination."""
    return await service.list_items(skip=skip, limit=limit)
```

### Endpoint Checklist

- [ ] Define route with appropriate HTTP method
- [ ] Add request/response schemas
- [ ] Implement input validation
- [ ] Add authentication dependency
- [ ] Handle errors appropriately
- [ ] Add docstring
- [ ] Update API documentation

## Database Migrations

### Creating a Migration

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "description of changes"

# Review the generated migration in alembic/versions/
```

### Applying Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Apply to specific version
alembic upgrade <revision>

# Rollback one step
alembic downgrade -1
```

### Migration Best Practices

1. Always review auto-generated migrations
2. Add data migrations separately from schema changes
3. Test rollback before deploying
4. Keep migrations atomic

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/backend/test_health.py

# Run specific test
pytest tests/backend/test_health.py::test_health_returns_200

# Run in watch mode
pytest-watch
```

### Writing Tests

```python
# tests/backend/test_new_module.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_entity(client: AsyncClient):
    response = await client.post(
        "/api/v1/new-module/",
        json={"name": "Test Entity"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Entity"
    assert "id" in data

@pytest.mark.asyncio
async def test_get_entity(client: AsyncClient):
    # First create
    create_response = await client.post(
        "/api/v1/new-module/",
        json={"name": "Test"},
    )
    entity_id = create_response.json()["id"]

    # Then get
    response = await client.get(f"/api/v1/new-module/{entity_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Test"
```

### Test Types

| Type | Location | Purpose |
|------|----------|---------|
| Unit | `tests/unit/` | Test individual functions |
| Integration | `tests/integration/` | Test component interactions |
| E2E | `tests/e2e/` | Test full user flows |

## Code Style

### Python

- Follow PEP 8
- Use type hints everywhere
- Maximum line length: 88 characters
- Use Ruff for linting: `ruff check app/`
- Use Ruff for formatting: `ruff format app/`

### TypeScript

- Follow ESLint rules
- Use strict TypeScript
- Prefer functional components
- Use proper typing (avoid `any`)

### Git Conventions

```
feat: add new user registration endpoint
fix: resolve database connection issue
docs: update API documentation
style: format code with ruff
refactor: extract common validation logic
test: add tests for user service
chore: update dependencies
```

## Debugging

### Backend Debugging

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with debugger
python -m debugpy --listen 5678 -m uvicorn app.main:app --reload
```

### Frontend Debugging

```bash
# Enable source maps in .env.local
NEXT_PUBLIC_DEBUG=true

# Use React DevTools browser extension
```

### Database Debugging

```bash
# Connect to database
psql postgresql://forgeai:forgeai_dev_password@localhost:5432/forgeai

# View queries (SQLAlchemy)
export ECHO_SQL=true
```

### Common Issues

| Issue | Solution |
|-------|----------|
| Import errors | Check `__init__.py` files exist |
| Type errors | Run `mypy app/` |
| Lint errors | Run `ruff check app/ --fix` |
| Test failures | Check fixtures in `conftest.py` |

## Performance Profiling

```bash
# Python profiling
python -m cProfile -o profile.stats uvicorn app.main:app

# Analyze
python -m pstats profile.stats

# Memory profiling
pip install memory_profiler
python -m memory_profiler app/main.py
```

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0](https://docs.sqlalchemy.org/)
- [Pydantic v2](https://docs.pydantic.dev/)
- [Next.js Documentation](https://nextjs.org/docs)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)

---

*For questions or issues, check the [Contributing Guide](Contributing.md) or open a GitHub issue.*
