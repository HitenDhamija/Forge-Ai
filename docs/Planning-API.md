# Planning API Reference

Base URL: `http://localhost:8000/api/v1`

All endpoints require JWT authentication unless otherwise noted.

## Authentication

Include the JWT token in the `Authorization` header:

```
Authorization: Bearer <your-jwt-token>
```

---

## Plans

### Create Plan

Create a new execution plan from a natural-language objective.

**Endpoint:** `POST /planner/plans`

**Request Body:**

```json
{
  "title": "Add user authentication",
  "description": "Implement JWT-based authentication with login, registration, and password reset endpoints",
  "goals": [
    "Secure all API endpoints with JWT validation",
    "Support user registration and login flows",
    "Implement password reset functionality"
  ],
  "context": {
    "framework": "FastAPI",
    "database": "PostgreSQL",
    "existing_auth": false
  },
  "constraints": [
    "Must be backward compatible with existing API",
    "No downtime during deployment"
  ]
}
```

**Request Schema:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | Yes | Plan title (1-255 characters) |
| `description` | string | Yes | Natural-language objective (min 1 character) |
| `goals` | array[string] | No | Specific goals to achieve |
| `context` | object | No | Additional context key-value pairs |
| `constraints` | array[string] | No | Limitations or requirements |

**Response:** `200 OK`

```json
{
  "status": "success",
  "message": "Plan created successfully",
  "data": {
    "id": "plan-a1b2c3d4e5f6",
    "title": "Add user authentication",
    "description": "Implement JWT-based authentication with login, registration, and password reset endpoints",
    "status": "draft",
    "tasks": [
      {
        "id": "task-000-a1b2c3d4",
        "title": "Analyze requirements",
        "description": "Analyze requirements related to authentication, jwt, login.",
        "task_type": "research",
        "priority": "high",
        "status": "pending",
        "complexity": "medium",
        "estimated_hours": 2.0,
        "dependencies": [],
        "tags": ["authentication", "jwt", "login"],
        "metadata": {
          "template_index": 0,
          "source": "decomposition"
        }
      },
      {
        "id": "task-001-b2c3d4e5",
        "title": "Design implementation approach",
        "description": "Design implementation approach related to authentication, jwt, login.",
        "task_type": "research",
        "priority": "high",
        "status": "pending",
        "complexity": "medium",
        "estimated_hours": 1.5,
        "dependencies": [],
        "tags": ["authentication", "jwt", "login"],
        "metadata": {
          "template_index": 1,
          "source": "decomposition"
        }
      }
    ],
    "dependencies": [
      {
        "task_id": "task-000-a1b2c3d4",
        "dependent_task_id": "task-002-c3d4e5f6",
        "dependency_type": "blocks",
        "description": "Analyze requirements blocks Implement core functionality"
      }
    ],
    "risks": [
      {
        "id": "risk-000",
        "title": "Security risk detected",
        "description": "Found 3 risk indicators for security across 2 task(s)",
        "risk_level": "high",
        "affected_tasks": ["task-000-a1b2c3d4", "task-002-c3d4e5f6"],
        "mitigation": "Conduct security review and follow security best practices",
        "probability": 0.3,
        "impact": 0.9,
        "category": "security"
      }
    ],
    "complexity": {
      "level": "medium",
      "score": 3.5,
      "factors": [
        "Moderate task count (7)",
        "Moderate task type diversity (4 types)",
        "Contains critical tasks (1)",
        "Moderate estimated effort (15.0 hours)"
      ],
      "estimated_total_hours": 17.3,
      "task_count": 7,
      "avg_task_complexity": 2.1
    },
    "intent": {
      "intent": "feature_development",
      "confidence": 0.82,
      "sub_intents": [],
      "reasoning": "Classified as feature_development (score: 0.60) based on keywords: implement, authentication",
      "keywords": ["implement", "authentication"]
    },
    "metadata": {
      "generator_version": "1.0.0",
      "intent": "feature_development",
      "confidence": 0.82,
      "context": {
        "framework": "FastAPI",
        "database": "PostgreSQL"
      }
    },
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-15T10:30:00Z",
    "estimated_total_hours": 17.3
  }
}
```

**Error Responses:**

| Status | Code | Description |
|--------|------|-------------|
| 400 | `VALIDATION_ERROR` | Invalid request body |
| 500 | `PLANNING_ERROR` | Plan generation failed |

**curl Example:**

```bash
curl -X POST http://localhost:8000/api/v1/planner/plans \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Add user authentication",
    "description": "Implement JWT-based authentication",
    "context": {"framework": "FastAPI"}
  }'
```

---

### List Plans

Get all plans with pagination.

**Endpoint:** `GET /planner/plans`

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | `1` | Page number (1-indexed) |
| `per_page` | integer | `20` | Items per page (max 100) |

**Response:** `200 OK`

```json
{
  "status": "success",
  "message": "Found 2 plans",
  "data": [
    {
      "id": "plan-a1b2c3d4e5f6",
      "title": "Add user authentication",
      "description": "Implement JWT-based authentication",
      "status": "draft",
      "tasks": [],
      "dependencies": [],
      "risks": [],
      "complexity": null,
      "intent": null,
      "metadata": {},
      "created_at": "2025-01-15T10:30:00Z",
      "updated_at": "2025-01-15T10:30:00Z",
      "estimated_total_hours": 17.3
    }
  ]
}
```

**curl Example:**

```bash
curl "http://localhost:8000/api/v1/planner/plans?page=1&per_page=10" \
  -H "Authorization: Bearer $TOKEN"
```

---

### Get Plan

Retrieve a specific plan by ID.

**Endpoint:** `GET /planner/plans/{plan_id}`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `plan_id` | string | Plan ID (e.g., `plan-a1b2c3d4e5f6`) |

**Response:** `200 OK`

```json
{
  "status": "success",
  "message": "Plan retrieved successfully",
  "data": {
    "id": "plan-a1b2c3d4e5f6",
    "title": "Add user authentication",
    "description": "Implement JWT-based authentication",
    "status": "active",
    "tasks": [
      {
        "id": "task-000-a1b2c3d4",
        "title": "Analyze requirements",
        "description": "Analyze requirements related to authentication.",
        "task_type": "research",
        "priority": "high",
        "status": "completed",
        "complexity": "medium",
        "estimated_hours": 2.0,
        "dependencies": [],
        "tags": ["authentication"],
        "metadata": {}
      }
    ],
    "dependencies": [],
    "risks": [],
    "complexity": {
      "level": "medium",
      "score": 3.5,
      "factors": ["Moderate task count (7)"],
      "estimated_total_hours": 17.3,
      "task_count": 7,
      "avg_task_complexity": 2.1
    },
    "intent": {
      "intent": "feature_development",
      "confidence": 0.82,
      "sub_intents": [],
      "reasoning": "Classified as feature_development",
      "keywords": ["implement", "authentication"]
    },
    "metadata": {},
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-15T10:35:00Z",
    "estimated_total_hours": 17.3
  }
}
```

**Errors:**

| Status | Code | Description |
|--------|------|-------------|
| 404 | `PLAN_NOT_FOUND` | Plan does not exist |

**curl Example:**

```bash
curl http://localhost:8000/api/v1/planner/plans/plan-a1b2c3d4e5f6 \
  -H "Authorization: Bearer $TOKEN"
```

---

### Update Plan

Update an existing plan's title, description, status, or metadata.

**Endpoint:** `PUT /planner/plans/{plan_id}`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `plan_id` | string | Plan ID |

**Request Body:**

```json
{
  "title": "Updated plan title",
  "description": "Updated description",
  "status": "active",
  "metadata": {
    "assignee": "team-alpha",
    "sprint": "S24"
  }
}
```

**Request Schema:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | No | New plan title |
| `description` | string | No | New description |
| `status` | string | No | New status (see valid transitions below) |
| `metadata` | object | No | Additional metadata (merged with existing) |

**Valid Status Transitions:**

| Current Status | Allowed Next Statuses |
|---------------|----------------------|
| `draft` | `active`, `cancelled` |
| `active` | `completed`, `failed`, `cancelled` |
| `completed` | (none) |
| `failed` | `active` |
| `cancelled` | `draft` |

**Response:** `200 OK`

```json
{
  "status": "success",
  "message": "Plan updated successfully",
  "data": {
    "id": "plan-a1b2c3d4e5f6",
    "title": "Updated plan title",
    "description": "Updated description",
    "status": "active",
    "metadata": {
      "assignee": "team-alpha",
      "sprint": "S24"
    },
    "updated_at": "2025-01-15T12:00:00Z"
  }
}
```

**Errors:**

| Status | Code | Description |
|--------|------|-------------|
| 404 | `PLAN_NOT_FOUND` | Plan does not exist |
| 400 | `PLANNING_ERROR` | Invalid status transition |

**curl Example:**

```bash
curl -X PUT http://localhost:8000/api/v1/planner/plans/plan-a1b2c3d4e5f6 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "active"}'
```

---

### Delete Plan

Delete a plan permanently.

**Endpoint:** `DELETE /planner/plans/{plan_id}`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `plan_id` | string | Plan ID |

**Response:** `200 OK`

```json
{
  "status": "success",
  "message": "Plan deleted successfully",
  "data": {
    "deleted": true,
    "plan_id": "plan-a1b2c3d4e5f6"
  }
}
```

**Errors:**

| Status | Code | Description |
|--------|------|-------------|
| 404 | `PLAN_NOT_FOUND` | Plan does not exist |

**curl Example:**

```bash
curl -X DELETE http://localhost:8000/api/v1/planner/plans/plan-a1b2c3d4e5f6 \
  -H "Authorization: Bearer $TOKEN"
```

---

## History

### Get Plan History

Get history entries for a specific plan.

**Endpoint:** `GET /planner/plans/{plan_id}/history`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `plan_id` | string | Plan ID |

**Response:** `200 OK`

```json
{
  "status": "success",
  "message": "Found 2 history entries",
  "data": [
    {
      "plan_id": "plan-a1b2c3d4e5f6",
      "action": "created",
      "timestamp": "2025-01-15T10:30:00Z",
      "details": {
        "title": "Add user authentication"
      },
      "user_id": null
    },
    {
      "plan_id": "plan-a1b2c3d4e5f6",
      "action": "updated",
      "timestamp": "2025-01-15T12:00:00Z",
      "details": {
        "fields": {
          "status": "active"
        }
      },
      "user_id": null
    }
  ]
}
```

---

### List All History

Get all history entries across all plans.

**Endpoint:** `GET /planner/history`

**Response:** `200 OK`

```json
{
  "status": "success",
  "message": "Found 5 history entries",
  "data": [
    {
      "plan_id": "plan-a1b2c3d4e5f6",
      "action": "created",
      "timestamp": "2025-01-15T10:30:00Z",
      "details": {"title": "Add user authentication"},
      "user_id": null
    },
    {
      "plan_id": "plan-b2c3d4e5f6a1",
      "action": "created",
      "timestamp": "2025-01-15T11:00:00Z",
      "details": {"title": "Fix login bug"},
      "user_id": null
    }
  ]
}
```

---

## Schemas

### PlanCreateRequest

```json
{
  "title": "string (required, 1-255 chars)",
  "description": "string (required, min 1 char)",
  "goals": ["string"],
  "context": {"key": "value"},
  "constraints": ["string"]
}
```

### PlanUpdateRequest

```json
{
  "title": "string (optional)",
  "description": "string (optional)",
  "status": "string (optional, enum: draft|active|completed|failed|cancelled)",
  "metadata": {"key": "value"}
}
```

### Plan Response Object

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique plan identifier |
| `title` | string | Plan title |
| `description` | string | Plan description |
| `status` | string | Current status |
| `tasks` | array[Task] | List of tasks |
| `dependencies` | array[DependencyInfo] | Dependency relationships |
| `risks` | array[RiskItem] | Identified risks |
| `complexity` | ComplexityAnalysis | Complexity assessment |
| `intent` | IntentClassification | Intent classification result |
| `metadata` | object | Custom metadata |
| `created_at` | datetime | Creation timestamp |
| `updated_at` | datetime | Last update timestamp |
| `estimated_total_hours` | float | Total estimated hours |

### Task Object

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique task identifier |
| `title` | string | Task title |
| `description` | string | Task description |
| `task_type` | string | Type (implementation, testing, documentation, review, deployment, configuration, research, refactoring) |
| `priority` | string | Priority (critical, high, medium, low) |
| `status` | string | Status (pending, in_progress, completed, failed, blocked, skipped) |
| `complexity` | string | Complexity (simple, medium, complex, very_complex) |
| `estimated_hours` | float | Estimated hours |
| `dependencies` | array[string] | IDs of blocking tasks |
| `tags` | array[string] | Task tags |
| `metadata` | object | Custom metadata |

### RiskItem Object

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique risk identifier |
| `title` | string | Risk title |
| `description` | string | Risk description |
| `risk_level` | string | Level (low, medium, high, critical) |
| `affected_tasks` | array[string] | Task IDs affected |
| `mitigation` | string | Mitigation strategy |
| `probability` | float | Probability (0.0 - 1.0) |
| `impact` | float | Impact (0.0 - 1.0) |
| `category` | string | Risk category |

---

## Error Response Format

All errors follow a consistent format:

```json
{
  "status": "error",
  "message": "Human-readable error message",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

For validation errors:

```json
{
  "status": "error",
  "message": "Validation failed",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid request body |
| `PLAN_NOT_FOUND` | 404 | Plan does not exist |
| `PLANNING_ERROR` | 500 | Internal planning error |
| `UNAUTHORIZED` | 401 | Missing or invalid authentication |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |

## Rate Limiting

API endpoints are rate limited:

| Endpoint | Requests/min |
|----------|-------------|
| `POST /plans` | 10 |
| `GET /plans` | 60 |
| `PUT /plans` | 20 |
| `DELETE /plans` | 20 |

Rate limit headers:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 59
X-RateLimit-Reset: 1718467200
```

---

## SDK Examples

### Python

```python
import httpx

async def create_plan():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/planner/plans",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": "Add user authentication",
                "description": "Implement JWT-based authentication",
                "context": {"framework": "FastAPI"}
            }
        )
        return response.json()

async def get_plan(plan_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"http://localhost:8000/api/v1/planner/plans/{plan_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        return response.json()
```

### cURL

```bash
# Create plan
curl -X POST http://localhost:8000/api/v1/planner/plans \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Add user authentication",
    "description": "Implement JWT-based authentication"
  }'

# List plans
curl http://localhost:8000/api/v1/planner/plans \
  -H "Authorization: Bearer $TOKEN"

# Get specific plan
curl http://localhost:8000/api/v1/planner/plans/plan-a1b2c3d4e5f6 \
  -H "Authorization: Bearer $TOKEN"

# Update plan status
curl -X PUT http://localhost:8000/api/v1/planner/plans/plan-a1b2c3d4e5f6 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "active"}'

# Delete plan
curl -X DELETE http://localhost:8000/api/v1/planner/plans/plan-a1b2c3d4e5f6 \
  -H "Authorization: Bearer $TOKEN"

# Get plan history
curl http://localhost:8000/api/v1/planner/plans/plan-a1b2c3d4e5f6/history \
  -H "Authorization: Bearer $TOKEN"
```
