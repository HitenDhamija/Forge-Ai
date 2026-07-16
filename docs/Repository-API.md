# Repository Intelligence API Reference

Base URL: `http://localhost:8000/api/v1`

All endpoints require JWT authentication unless otherwise noted.

## Authentication

Include the JWT token in the `Authorization` header:

```
Authorization: Bearer <your-jwt-token>
```

---

## Repositories

### Create Repository

Import a new repository for analysis.

**Endpoint:** `POST /repositories`

**Request Body:**

```json
{
  "name": "my-project",
  "description": "A sample project for analysis",
  "import_method": "git",
  "source_url": "https://github.com/user/repo.git",
  "source_path": null
}
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Repository name (1-255 characters) |
| `description` | string | No | Optional description |
| `import_method` | enum | Yes | One of: `zip`, `git`, `folder` |
| `source_url` | string | Conditional | URL for git import |
| `source_path` | string | Conditional | Local path for folder import |

**Response:** `201 Created`

```json
{
  "id": "abc123-def456",
  "name": "my-project",
  "description": "A sample project for analysis",
  "status": "importing",
  "import_method": "git",
  "source_url": "https://github.com/user/repo.git",
  "local_path": "/tmp/forgeai/repos/abc123-def456",
  "created_at": "2025-01-15T10:30:00Z",
  "analyzed_at": null,
  "error_message": null
}
```

**Errors:**

| Status | Code | Description |
|--------|------|-------------|
| 400 | `VALIDATION_ERROR` | Invalid request body |
| 413 | `REPOSITORY_TOO_LARGE` | Repository exceeds size limit |
| 500 | `IMPORT_FAILED` | Import operation failed |

**curl Example:**

```bash
curl -X POST http://localhost:8000/api/v1/repositories \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-project",
    "import_method": "git",
    "source_url": "https://github.com/user/repo.git"
  }'
```

---

### List Repositories

Get all repositories for the current user.

**Endpoint:** `GET /repositories`

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `skip` | integer | `0` | Pagination offset |
| `limit` | integer | `20` | Results per page (max 100) |
| `status` | string | - | Filter by status: `importing`, `analyzing`, `ready`, `error` |

**Response:** `200 OK`

```json
{
  "items": [
    {
      "id": "abc123-def456",
      "name": "my-project",
      "description": "A sample project",
      "status": "ready",
      "import_method": "git",
      "source_url": "https://github.com/user/repo.git",
      "local_path": "/tmp/forgeai/repos/abc123-def456",
      "created_at": "2025-01-15T10:30:00Z",
      "analyzed_at": "2025-01-15T10:35:00Z"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 20
}
```

**curl Example:**

```bash
curl http://localhost:8000/api/v1/repositories \
  -H "Authorization: Bearer $TOKEN"
```

---

### Get Repository

Get details for a specific repository.

**Endpoint:** `GET /repositories/{repository_id}`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `repository_id` | string | Repository ID |

**Response:** `200 OK`

```json
{
  "id": "abc123-def456",
  "name": "my-project",
  "description": "A sample project",
  "status": "ready",
  "import_method": "git",
  "source_url": "https://github.com/user/repo.git",
  "local_path": "/tmp/forgeai/repos/abc123-def456",
  "created_at": "2025-01-15T10:30:00Z",
  "analyzed_at": "2025-01-15T10:35:00Z",
  "error_message": null
}
```

**Errors:**

| Status | Code | Description |
|--------|------|-------------|
| 404 | `REPOSITORY_NOT_FOUND` | Repository does not exist |

**curl Example:**

```bash
curl http://localhost:8000/api/v1/repositories/abc123-def456 \
  -H "Authorization: Bearer $TOKEN"
```

---

### Delete Repository

Remove a repository and its analysis data.

**Endpoint:** `DELETE /repositories/{repository_id}`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `repository_id` | string | Repository ID |

**Response:** `204 No Content`

**Errors:**

| Status | Code | Description |
|--------|------|-------------|
| 404 | `REPOSITORY_NOT_FOUND` | Repository does not exist |

**curl Example:**

```bash
curl -X DELETE http://localhost:8000/api/v1/repositories/abc123-def456 \
  -H "Authorization: Bearer $TOKEN"
```

---

## Analysis

### Trigger Analysis

Start or re-run analysis on a repository.

**Endpoint:** `POST /repositories/{repository_id}/analyze`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `repository_id` | string | Repository ID |

**Request Body:**

```json
{
  "force": false,
  "options": {
    "deep_analysis": true,
    "include_tests": false
  }
}
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `force` | boolean | No | Force re-analysis (default: false) |
| `options.deep_analysis` | boolean | No | Enable deep AST analysis |
| `options.include_tests` | boolean | No | Include test files in analysis |

**Response:** `202 Accepted`

```json
{
  "message": "Analysis started",
  "repository_id": "abc123-def456",
  "status": "analyzing"
}
```

**Errors:**

| Status | Code | Description |
|--------|------|-------------|
| 404 | `REPOSITORY_NOT_FOUND` | Repository does not exist |
| 409 | `ANALYSIS_IN_PROGRESS` | Analysis already running |

**curl Example:**

```bash
curl -X POST http://localhost:8000/api/v1/repositories/abc123-def456/analyze \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"force": false}'
```

---

### Get Analysis Results

Retrieve completed analysis results.

**Endpoint:** `GET /repositories/{repository_id}/analysis`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `repository_id` | string | Repository ID |

**Response:** `200 OK`

```json
{
  "repository_id": "abc123-def456",
  "analyzed_at": "2025-01-15T10:35:00Z",
  "languages": [
    {
      "name": "Python",
      "file_count": 45,
      "total_lines": 12500,
      "percentage": 72.5,
      "extensions": [".py", ".pyi"]
    },
    {
      "name": "TypeScript",
      "file_count": 18,
      "total_lines": 4700,
      "percentage": 27.5,
      "extensions": [".ts", ".tsx"]
    }
  ],
  "frameworks": [
    {
      "name": "FastAPI",
      "version": "0.115.0",
      "confidence": 0.95,
      "evidence": [
        "Dependency: fastapi in pyproject.toml",
        "Pattern: @app.get in main.py",
        "Pattern: APIRouter in routes/"
      ]
    }
  ],
  "dependencies": [
    {
      "name": "fastapi",
      "version": ">=0.115.0",
      "is_production": true,
      "source_file": "pyproject.toml"
    }
  ],
  "folder_structure": [
    {
      "name": "src",
      "path": "src/",
      "purpose": "source_code",
      "file_count": 45,
      "children": []
    }
  ],
  "architecture": {
    "style": "clean",
    "description": "Clean architecture with domain, application, and infrastructure layers",
    "entry_points": ["src/main.py"],
    "main_modules": ["domain", "application", "infrastructure"],
    "authentication_detected": true,
    "database_detected": true,
    "api_detected": true,
    "frontend_detected": false
  },
  "code_elements": [
    {
      "name": "UserService",
      "type": "class",
      "file_path": "src/application/services/user_service.py",
      "line_start": 15,
      "line_end": 89,
      "docstring": "Service for user operations.",
      "decorators": [],
      "parent_class": "BaseService",
      "parameters": [],
      "return_type": null,
      "imports": [],
      "is_exported": true
    }
  ],
  "routes": [
    {
      "method": "GET",
      "path": "/api/v1/users",
      "function_name": "list_users",
      "file_path": "src/api/routes/users.py",
      "line_number": 12,
      "middleware": ["auth"],
      "authentication_required": true,
      "parameters": ["skip", "limit"],
      "response_model": "UserListResponse"
    }
  ],
  "database_models": [
    {
      "name": "User",
      "table_name": "users",
      "file_path": "src/infrastructure/models/user.py",
      "line_number": 10,
      "fields": [
        {
          "name": "id",
          "type": "Column",
          "file_path": "src/infrastructure/models/user.py",
          "line_start": 12,
          "line_end": 12
        }
      ],
      "relationships": ["roles", "posts"],
      "primary_key": "id",
      "foreign_keys": []
    }
  ],
  "import_graph": [
    {
      "source": "src/application/services/user_service.py",
      "target": "src/domain/repositories/user_repo.py",
      "file_path": "src/application/services/user_service.py"
    }
  ],
  "config_files": [
    "pyproject.toml",
    "alembic.ini",
    ".env.example"
  ],
  "entry_points": [
    "src/main.py",
    "src/worker.py"
  ],
  "total_files": 63,
  "total_lines": 17200,
  "analysis_time_ms": 4520.5
}
```

**Errors:**

| Status | Code | Description |
|--------|------|-------------|
| 404 | `REPOSITORY_NOT_FOUND` | Repository does not exist |
| 404 | `ANALYSIS_NOT_FOUND` | Analysis not yet completed |

**curl Example:**

```bash
curl http://localhost:8000/api/v1/repositories/abc123-def456/analysis \
  -H "Authorization: Bearer $TOKEN"
```

---

## Semantic Graph

### Get Full Graph

Retrieve the complete semantic graph for a repository.

**Endpoint:** `GET /repositories/{repository_id}/graph`

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `node_types` | string | - | Comma-separated node types to include |
| `max_depth` | integer | `3` | Maximum traversal depth |

**Response:** `200 OK`

```json
{
  "nodes": [
    {
      "id": "repo:abc123",
      "type": "repository",
      "name": "my-project",
      "metadata": {
        "url": "https://github.com/user/repo.git",
        "branch": "main"
      }
    },
    {
      "id": "folder:src",
      "type": "folder",
      "name": "src",
      "metadata": {
        "path": "src/",
        "purpose": "source_code"
      }
    },
    {
      "id": "module:src/main.py",
      "type": "module",
      "name": "main.py",
      "metadata": {
        "language": "Python",
        "lines": 150
      }
    },
    {
      "id": "class:UserService",
      "type": "class",
      "name": "UserService",
      "metadata": {
        "parent": "BaseService",
        "methods": ["get_user", "create_user", "delete_user"]
      }
    }
  ],
  "edges": [
    {
      "source": "repo:abc123",
      "target": "folder:src",
      "relationship": "contains"
    },
    {
      "source": "folder:src",
      "target": "module:src/main.py",
      "relationship": "contains"
    },
    {
      "source": "module:src/main.py",
      "target": "class:UserService",
      "relationship": "defines"
    }
  ],
  "root_id": "repo:abc123"
}
```

**curl Example:**

```bash
curl "http://localhost:8000/api/v1/repositories/abc123-def456/graph?node_types=module,class" \
  -H "Authorization: Bearer $TOKEN"
```

---

### Get Graph Nodes

Retrieve all nodes of a specific type.

**Endpoint:** `GET /repositories/{repository_id}/graph/nodes`

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `type` | string | No | Filter by node type |
| `name` | string | No | Filter by name (substring match) |

**Response:** `200 OK`

```json
{
  "nodes": [
    {
      "id": "class:UserService",
      "type": "class",
      "name": "UserService",
      "metadata": {
        "parent": "BaseService",
        "methods": ["get_user", "create_user", "delete_user"],
        "file_path": "src/application/services/user_service.py"
      }
    }
  ],
  "total": 1
}
```

---

### Get Graph Edges

Retrieve all edges for a specific node.

**Endpoint:** `GET /repositories/{repository_id}/graph/edges`

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `node_id` | string | Yes | Node ID to get edges for |
| `direction` | string | No | `outgoing` (default), `incoming`, or `both` |

**Response:** `200 OK`

```json
{
  "edges": [
    {
      "source": "class:UserService",
      "target": "class:UserRepository",
      "relationship": "depends_on"
    },
    {
      "source": "module:main.py",
      "target": "class:UserService",
      "relationship": "defines"
    }
  ],
  "total": 2
}
```

---

### Search Graph

Search the graph for nodes matching a query.

**Endpoint:** `GET /repositories/{repository_id}/graph/search`

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `q` | string | Yes | Search query |
| `type` | string | No | Filter by node type |
| `limit` | integer | No | Max results (default: 20) |

**Response:** `200 OK`

```json
{
  "results": [
    {
      "node": {
        "id": "class:UserService",
        "type": "class",
        "name": "UserService",
        "metadata": {}
      },
      "score": 0.95,
      "highlights": {
        "name": "<mark>User</mark>Service"
      }
    }
  ],
  "total": 1
}
```

---

## Health

### Health Check

Check if the repository intelligence service is available.

**Endpoint:** `GET /health`

**Response:** `200 OK`

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "environment": "development"
}
```

**Note:** This endpoint does not require authentication.

---

## Rate Limiting (Future)

Rate limits will be applied per-user:

| Tier | Requests/min | Requests/hour |
|------|-------------|---------------|
| Free | 60 | 1000 |
| Pro | 300 | 10000 |
| Enterprise | Custom | Custom |

Rate limit headers:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 59
X-RateLimit-Reset: 1705312200
```

---

## Error Response Format

All errors follow a consistent format:

```json
{
  "detail": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "status": 400,
    "fields": null
  }
}
```

For validation errors:

```json
{
  "detail": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "status": 422,
    "fields": {
      "name": "Field is required",
      "source_url": "Must be a valid URL"
    }
  }
}
```

---

## Pagination

List endpoints support pagination:

```json
{
  "items": [...],
  "total": 150,
  "skip": 0,
  "limit": 20
}
```

Use `skip` and `limit` query parameters:

```
GET /repositories?skip=20&limit=20  (page 2)
GET /repositories?skip=40&limit=20  (page 3)
```
