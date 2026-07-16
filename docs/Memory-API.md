# Memory API Reference

## Overview

The ForgeAI Semantic Memory API provides endpoints for storing, retrieving, and managing semantic memories. All endpoints are prefixed with `/api/v1/memory`.

## Authentication

All API endpoints require authentication via JWT token:

```http
Authorization: Bearer <your-jwt-token>
```

## Endpoints

### POST /api/v1/memory/index

Index new memories into the semantic memory store.

**Request Body**:
```json
{
  "memories": [
    {
      "content": "The quick brown fox jumps over the lazy dog",
      "metadata": {
        "source": "conversation",
        "session_id": "abc-123",
        "importance": 0.8,
        "tags": ["example", "pangram"]
      }
    }
  ],
  "collection": "conversations",
  "chunk_strategy": "semantic"
}
```

**Request Schema**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| memories | array | Yes | Array of memory objects |
| memories[].content | string | Yes | Text content to index |
| memories[].metadata | object | No | Additional metadata |
| collection | string | No | Target collection (default: "default") |
| chunk_strategy | string | No | Chunking strategy: "semantic", "fixed", "paragraph" |

**Response** (201 Created):
```json
{
  "status": "success",
  "data": {
    "indexed": 3,
    "collection": "conversations",
    "memory_ids": [
      "mem-uuid-1",
      "mem-uuid-2",
      "mem-uuid-3"
    ],
    "processing_time_ms": 245
  }
}
```

**Error Responses**:

400 Bad Request:
```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid memory format",
    "details": {
      "field": "content",
      "issue": "Content cannot be empty"
    }
  }
}
```

413 Payload Too Large:
```json
{
  "status": "error",
  "error": {
    "code": "PAYLOAD_TOO_LARGE",
    "message": "Total content size exceeds 10MB limit"
  }
}
```

**Example** (Python):
```python
import httpx

async def index_memories():
    response = await client.post(
        "/api/v1/memory/index",
        json={
            "memories": [
                {
                    "content": "Important meeting notes from today...",
                    "metadata": {
                        "source": "meeting",
                        "importance": 0.9
                    }
                }
            ],
            "collection": "work_notes"
        }
    )
    return response.json()
```

---

### POST /api/v1/memory/search

Perform semantic search across memories.

**Request Body**:
```json
{
  "query": "machine learning algorithms",
  "collection": "conversations",
  "top_k": 10,
  "filters": {
    "source": "documentation",
    "tags": ["python", "ml"],
    "importance_min": 0.5,
    "created_after": "2024-01-01T00:00:00Z"
  },
  "include_metadata": true,
  "rerank": true
}
```

**Request Schema**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| query | string | Yes | Search query |
| collection | string | No | Collection to search (default: all) |
| top_k | integer | No | Number of results (default: 10, max: 100) |
| filters | object | No | Metadata filters |
| include_metadata | boolean | No | Include metadata in response (default: true) |
| rerank | boolean | No | Apply reranking (default: true) |

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "results": [
      {
        "id": "mem-uuid-1",
        "content": "Machine learning is a subset of artificial intelligence...",
        "score": 0.92,
        "metadata": {
          "source": "documentation",
          "timestamp": "2024-06-15T10:30:00Z",
          "importance": 0.85,
          "tags": ["ml", "ai"]
        }
      },
      {
        "id": "mem-uuid-2",
        "content": "Supervised learning uses labeled datasets...",
        "score": 0.87,
        "metadata": {
          "source": "conversation",
          "timestamp": "2024-06-14T15:45:00Z",
          "importance": 0.7,
          "tags": ["ml", "supervised"]
        }
      }
    ],
    "total_results": 2,
    "query_classification": "conceptual",
    "processing_time_ms": 128
  }
}
```

**Filter Operators**:
- `source`: Exact match
- `tags`: Contains any of the listed tags
- `importance_min` / `importance_max`: Range filter
- `created_after` / `created_before`: Temporal filter
- `session_id`: Exact match

**Example** (JavaScript):
```javascript
const searchMemories = async (query) => {
  const response = await fetch('/api/v1/memory/search', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      query: query,
      top_k: 5,
      filters: {
        source: 'conversation',
        importance_min: 0.6
      }
    })
  });
  return response.json();
};
```

---

### POST /api/v1/memory/context

Retrieve contextually relevant memories for a query, optimized for LLM consumption.

**Request Body**:
```json
{
  "query": "How do I implement authentication in FastAPI?",
  "max_tokens": 4096,
  "collection": "code",
  "include_related": true,
  "format": "structured"
}
```

**Request Schema**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| query | string | Yes | Context query |
| max_tokens | integer | No | Maximum tokens in response (default: 4096) |
| collection | string | No | Collection to search |
| include_related | boolean | No | Include related memories (default: true) |
| format | string | No | Response format: "structured", "plain", "json" |

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "context": {
      "query": "How do I implement authentication in FastAPI?",
      "classification": "procedural",
      "memories": [
        {
          "topic": "FastAPI Authentication",
          "memories": [
            {
              "id": "mem-uuid-1",
              "content": "To implement JWT authentication in FastAPI...",
              "importance": 0.95,
              "age_days": 5
            },
            {
              "id": "mem-uuid-2",
              "content": "Use OAuth2PasswordBearer for token validation...",
              "importance": 0.88,
              "age_days": 3
            }
          ],
          "relevance_score": 0.94
        },
        {
          "topic": "Security Best Practices",
          "memories": [
            {
              "id": "mem-uuid-3",
              "content": "Always hash passwords using bcrypt...",
              "importance": 0.82,
              "age_days": 10
            }
          ],
          "relevance_score": 0.78
        }
      ],
      "summary": "Based on 4 relevant memories spanning 10 days.",
      "token_count": 1247
    },
    "processing_time_ms": 89
  }
}
```

**Context Format Options**:

`structured`: Grouped by topic with metadata
```json
{
  "topic": "Topic Name",
  "memories": [...],
  "relevance_score": 0.9
}
```

`plain`: Simple text format
```
[Memory 1] Content here...
[Memory 2] Content here...
```

`json`: Raw JSON array of memories

---

### POST /api/v1/memory/related

Find memories related to given memory IDs.

**Request Body**:
```json
{
  "memory_ids": ["mem-uuid-1", "mem-uuid-2"],
  "depth": 2,
  "max_results": 10,
  "relationship_types": ["related_to", "supports"]
}
```

**Request Schema**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| memory_ids | array | Yes | Starting memory IDs |
| depth | integer | No | Traversal depth (default: 1, max: 3) |
| max_results | integer | No | Maximum results (default: 20) |
| relationship_types | array | No | Filter by relationship types |

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "related_memories": [
      {
        "id": "mem-uuid-3",
        "content": "Related content here...",
        "relationship": {
          "type": "supports",
          "source_id": "mem-uuid-1",
          "strength": 0.85
        }
      }
    ],
    "graph_stats": {
      "nodes_visited": 15,
      "edges_traversed": 22
    }
  }
}
```

**Relationship Types**:
| Type | Description |
|------|-------------|
| related_to | General semantic similarity |
| caused_by | Causal relationship |
| triggers | Temporal/sequential |
| contradicts | Conflicting information |
| supports | Supporting evidence |
| elaborates | Additional detail |

---

### GET /api/v1/memory/{memory_id}

Retrieve a specific memory by ID.

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| memory_id | string | Memory UUID |

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| include_related | boolean | false | Include related memories |
| format | string | "full" | Response format: "full", "summary" |

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "id": "mem-uuid-1",
    "content": "Full memory content here...",
    "embedding_id": "emb-uuid-1",
    "collection": "conversations",
    "metadata": {
      "source": "conversation",
      "timestamp": "2024-06-15T10:30:00Z",
      "importance": 0.85,
      "tags": ["important", "decision"],
      "session_id": "session-uuid-1"
    },
    "created_at": "2024-06-15T10:30:00Z",
    "updated_at": "2024-06-15T10:30:00Z"
  }
}
```

**Error Response** (404 Not Found):
```json
{
  "status": "error",
  "error": {
    "code": "MEMORY_NOT_FOUND",
    "message": "Memory with id 'mem-uuid-1' not found"
  }
}
```

---

### PUT /api/v1/memory/{memory_id}

Update memory metadata.

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| memory_id | string | Memory UUID |

**Request Body**:
```json
{
  "metadata": {
    "importance": 0.95,
    "tags": ["critical", "decision", "approved"]
  }
}
```

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "id": "mem-uuid-1",
    "updated_fields": ["metadata.importance", "metadata.tags"],
    "updated_at": "2024-06-15T12:00:00Z"
  }
}
```

---

### DELETE /api/v1/memory/{memory_id}

Delete a memory by ID.

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| memory_id | string | Memory UUID |

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "deleted": true,
    "id": "mem-uuid-1"
  }
}
```

**Error Response** (404 Not Found):
```json
{
  "status": "error",
  "error": {
    "code": "MEMORY_NOT_FOUND",
    "message": "Memory with id 'mem-uuid-1' not found"
  }
}
```

---

### GET /api/v1/memory/stats

Get collection statistics.

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| collection | string | null | Specific collection (default: all) |

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "collections": [
      {
        "name": "conversations",
        "count": 15420,
        "size_bytes": 524288000,
        "avg_importance": 0.72,
        "oldest_memory": "2024-01-15T00:00:00Z",
        "newest_memory": "2024-06-15T10:30:00Z"
      },
      {
        "name": "code",
        "count": 8930,
        "size_bytes": 312000000,
        "avg_importance": 0.68,
        "oldest_memory": "2024-02-01T00:00:00Z",
        "newest_memory": "2024-06-15T09:15:00Z"
      }
    ],
    "total_memories": 24350,
    "total_size_bytes": 836288000,
    "embeddings_indexed": 24350
  }
}
```

---

### POST /api/v1/memory/reindex

Trigger reindexing of a collection.

**Request Body**:
```json
{
  "collection": "conversations",
  "strategy": "full"
}
```

**Request Schema**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| collection | string | Yes | Collection to reindex |
| strategy | string | No | Reindex strategy: "full", "incremental" |

**Response** (202 Accepted):
```json
{
  "status": "success",
  "data": {
    "job_id": "reindex-uuid-1",
    "collection": "conversations",
    "strategy": "full",
    "status": "queued",
    "estimated_time_seconds": 300
  }
}
```

---

### DELETE /api/v1/memory/collection/{collection_name}

Delete an entire collection.

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| collection_name | string | Collection name |

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "deleted": true,
    "collection": "conversations",
    "memories_deleted": 15420
  }
}
```

---

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| VALIDATION_ERROR | 400 | Invalid request body |
| UNAUTHORIZED | 401 | Missing or invalid authentication |
| FORBIDDEN | 403 | Insufficient permissions |
| MEMORY_NOT_FOUND | 404 | Memory does not exist |
| COLLECTION_NOT_FOUND | 404 | Collection does not exist |
| PAYLOAD_TOO_LARGE | 413 | Request exceeds size limit |
| RATE_LIMIT_EXCEEDED | 429 | Too many requests |
| INTERNAL_ERROR | 500 | Server error |
| SERVICE_UNAVAILABLE | 503 | Memory service unavailable |

## Rate Limiting

API endpoints are rate limited:
- **Search/Context**: 100 requests/minute
- **Index**: 20 requests/minute
- **Delete**: 50 requests/minute
- **Read**: 200 requests/minute

Rate limit headers:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1718467200
```

## Pagination

List endpoints support pagination:

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| page | integer | 1 | Page number |
| page_size | integer | 20 | Items per page (max: 100) |

**Response Pagination**:
```json
{
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_items": 1542,
    "total_pages": 78
  }
}
```

## SDK Examples

### Python

```python
from forgeai import MemoryClient

client = MemoryClient(
    host="localhost",
    port=8000,
    api_key="your-api-key"
)

# Index memories
await client.index(
    content="Important meeting notes",
    collection="work",
    metadata={"importance": 0.9}
)

# Search
results = await client.search(
    query="meeting decisions",
    top_k=5,
    collection="work"
)

# Get context for LLM
context = await client.get_context(
    query="What were the action items from the meeting?",
    max_tokens=2048
)
```

### JavaScript/TypeScript

```typescript
import { MemoryClient } from '@forgeai/sdk';

const client = new MemoryClient({
  host: 'localhost',
  port: 8000,
  apiKey: 'your-api-key'
});

// Index memories
await client.index({
  content: 'Important meeting notes',
  collection: 'work',
  metadata: { importance: 0.9 }
});

// Search
const results = await client.search({
  query: 'meeting decisions',
  topK: 5,
  collection: 'work'
});

// Get context
const context = await client.getContext({
  query: 'What were the action items?',
  maxTokens: 2048
});
```

### cURL

```bash
# Index memory
curl -X POST http://localhost:8000/api/v1/memory/index \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "memories": [{"content": "Test memory"}],
    "collection": "test"
  }'

# Search
curl -X POST http://localhost:8000/api/v1/memory/search \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "test query", "top_k": 5}'

# Get context
curl -X POST http://localhost:8000/api/v1/memory/context \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "How do I do X?", "max_tokens": 2048}'
```
