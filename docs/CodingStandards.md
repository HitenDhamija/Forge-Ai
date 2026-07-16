# ForgeAI Coding Standards

## Python Standards

### Type Hints

Always use type hints for function signatures:

```python
# Good
def get_user(user_id: int) -> Optional[User]:
    ...

async def create_task(data: TaskCreate, user: User) -> Task:
    ...

# Bad
def get_user(user_id):
    ...
```

### Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Variables | snake_case | `user_name`, `task_count` |
| Functions | snake_case | `get_user_by_id`, `create_task` |
| Classes | PascalCase | `UserService`, `TaskRepository` |
| Constants | UPPER_SNAKE_CASE | `MAX_PAGE_SIZE`, `DEFAULT_TIMEOUT` |
| Private | _prefix | `_internal_method`, `_cache` |
| Protected | _prefix | `_protected_method` |

### Docstrings

Use Google-style docstrings:

```python
async def get_user_by_email(email: str) -> Optional[User]:
    """Retrieve a user by their email address.

    Args:
        email: The user's email address.

    Returns:
        The user if found, None otherwise.

    Raises:
        DatabaseError: If the database query fails.
    """
    ...
```

### Import Order

```python
# 1. Standard library
import os
from datetime import datetime
from typing import Optional

# 2. Third-party packages
import sqlalchemy as sa
from fastapi import APIRouter, Depends
from pydantic import BaseModel

# 3. Local application
from app.domain.entities.user import User
from app.services.user_service import UserService
```

### Error Handling

```python
# Good: Specific exceptions
class UserNotFoundError(Exception):
    pass

async def get_user(user_id: int) -> User:
    user = await repository.get_by_id(user_id)
    if not user:
        raise UserNotFoundError(f"User {user_id} not found")
    return user

# Bad: Generic exceptions
async def get_user(user_id: int):
    try:
        return await repository.get_by_id(user_id)
    except Exception:
        return None
```

### Async/Await

Always use async/await for I/O operations:

```python
# Good
async def get_users() -> List[User]:
    async with session.begin():
        result = await session.execute(select(User))
        return result.scalars().all()

# Bad
def get_users():
    with session.begin():
        result = session.execute(select(User))
        return result.scalars().all()
```

### Project Structure

```toml
# pyproject.toml
[tool.ruff]
line-length = 88
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP", "B"]

[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_configs = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

## TypeScript Standards

### Type Definitions

```typescript
// Good: Explicit types
interface User {
  id: number;
  email: string;
  createdAt: Date;
}

const getUser = async (id: number): Promise<User> => {
  const response = await fetch(`/api/users/${id}`);
  return response.json();
};

// Bad: Using `any`
const getUser = async (id: any): Promise<any> => {
  const response = await fetch(`/api/users/${id}`);
  return response.json();
};
```

### Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Variables | camelCase | `userName`, `taskCount` |
| Functions | camelCase | `getUserById`, `createTask` |
| Components | PascalCase | `UserProfile`, `TaskList` |
| Types/Interfaces | PascalCase | `UserType`, `TaskInterface` |
| Constants | UPPER_SNAKE_CASE | `MAX_PAGE_SIZE` |
| Files | camelCase | `userService.ts` |
| Components | PascalCase | `UserProfile.tsx` |

### React Components

```typescript
// Good: Functional component with types
interface ButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: 'primary' | 'secondary';
}

export const Button: React.FC<ButtonProps> = ({
  children,
  onClick,
  variant = 'primary',
}) => {
  return (
    <button
      className={`btn btn-${variant}`}
      onClick={onClick}
    >
      {children}
    </button>
  );
};

// Bad: Missing prop types
export const Button = ({ children, onClick, variant }) => {
  return (
    <button className={`btn btn-${variant}`} onClick={onClick}>
      {children}
    </button>
  );
};
```

### Hooks

```typescript
// Custom hook naming: use + PascalCase
export const useUser = (id: number) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchUser(id).then(setUser).finally(() => setLoading(false));
  }, [id]);

  return { user, loading };
};
```

### Error Boundaries

```typescript
// Always handle errors in async operations
const fetchData = async (): Promise<Data> => {
  try {
    const response = await fetch('/api/data');
    if (!response.ok) {
      throw new ApiError(response.status, 'Failed to fetch');
    }
    return await response.json();
  } catch (error) {
    console.error('Fetch error:', error);
    throw error;
  }
};
```

## Git Workflow

### Branch Naming

```
feat/user-authentication
fix/database-connection
docs/api-documentation
refactor/service-layer
test/user-service
chore/dependencies-update
```

### Commit Messages

Follow Conventional Commits:

```
feat: add user registration endpoint

- Implement POST /api/v1/auth/register
- Add email validation
- Hash passwords with bcrypt

Closes #123
```

```
fix: resolve database connection pool exhaustion

- Increase pool size from 10 to 20
- Add connection timeout handling
- Implement retry logic

Fixes #456
```

### Commit Types

| Type | Description |
|------|-------------|
| feat | New feature |
| fix | Bug fix |
| docs | Documentation changes |
| style | Code style changes (formatting, etc.) |
| refactor | Code refactoring |
| test | Adding or updating tests |
| chore | Maintenance tasks |

### PR Process

1. Create feature branch from `main`
2. Make changes with descriptive commits
3. Push branch and create PR
4. Fill out PR template completely
5. Request review from maintainers
6. Address review comments
7. Squash and merge when approved

### Commit Best Practices

- Keep commits atomic and focused
- Write clear commit messages
- Reference issues when applicable
- Never commit secrets or credentials
- Ensure tests pass before committing

## Code Review Checklist

### General

- [ ] Code follows style guidelines
- [ ] No commented-out code
- [ ] No hardcoded values
- [ ] Error handling is appropriate
- [ ] Logging is sufficient

### Python

- [ ] Type hints are present
- [ ] Docstrings are clear
- [ ] No unused imports
- [ ] Async/await used correctly
- [ ] Tests cover new code

### TypeScript

- [ ] Types are explicit
- [ ] No `any` types
- [ ] Components are properly typed
- [ ] Error boundaries implemented
- [ ] Performance considered

### Security

- [ ] No secrets in code
- [ ] Input validation present
- [ ] Authentication required where needed
- [ ] SQL injection prevented
- [ ] XSS protection implemented

---

*Adhere to these standards to maintain code quality and consistency across the project.*
