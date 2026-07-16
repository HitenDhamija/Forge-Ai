# API Reference

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication

All endpoints require JWT token in header:
```
Authorization: Bearer <token>
```

## Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /auth/login | Login |
| POST | /auth/register | Register |
| POST | /auth/refresh | Refresh token |

### Repositories

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /repositories | List repositories |
| POST | /repositories/import | Import repository |
| GET | /repositories/{id} | Get repository |
| DELETE | /repositories/{id} | Delete repository |
| GET | /repositories/{id}/summary | Get summary |
| GET | /repositories/{id}/analysis | Get analysis |

### Memory

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /memory/index | Index content |
| POST | /memory/search | Search memory |
| GET | /memory/context | Get context |
| GET | /memory/stats | Get statistics |

### Workflows

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /workflows | List workflows |
| POST | /workflows | Create workflow |
| GET | /workflows/{id} | Get workflow |
| POST | /workflows/{id}/start | Start workflow |
| POST | /workflows/{id}/pause | Pause workflow |
| POST | /workflows/{id}/resume | Resume workflow |
| POST | /workflows/{id}/cancel | Cancel workflow |

### Agents

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /agents | List agents |
| GET | /agents/{id} | Get agent |
| POST | /agents/{id}/execute | Execute task |

### Learning

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /learning/process | Process experience |
| GET | /learning/patterns | Get patterns |
| GET | /learning/experiences | Get experiences |
| GET | /learning/recommendations | Get recommendations |

### Monitoring

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /monitoring/overview | Get overview |
| GET | /monitoring/workflows | Get workflow stats |
| GET | /monitoring/agents | Get agent stats |
| GET | /monitoring/health | Health check |

### Studio

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /studio/workflows | List workflows |
| GET | /studio/prompts | List prompts |
| POST | /studio/prompts/{id}/test | Test prompt |

### Organizations

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /organizations | Create organization |
| GET | /organizations | List organizations |
| GET | /organizations/{id} | Get organization |
| POST | /organizations/{id}/repositories | Add repository |

### Plugins

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /plugins | List plugins |
| POST | /plugins/install | Install plugin |
| POST | /plugins/{id}/uninstall | Uninstall plugin |

### Developer Experience

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /developer/config | Get configuration |
| PUT | /developer/config | Update configuration |
| GET | /developer/diagnostics | Run diagnostics |
| POST | /developer/backup | Create backup |

### Validation

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /validation/system | Run system validation |
| GET | /validation/benchmark | Run benchmarks |
| GET | /validation/quality | Check quality gates |
| GET | /validation/security | Run security audit |

## Error Responses

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input",
    "details": {...}
  }
}
```

## Rate Limiting

- 100 requests per minute
- 1000 requests per hour
