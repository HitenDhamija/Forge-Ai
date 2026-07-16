# Deployment Guide

## Docker Compose Deployment

### Prerequisites
- Docker 24+
- Docker Compose v2+

### Quick Start

```bash
# Clone repository
git clone https://github.com/forgeai/forgeai.git
cd forgeai

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start services
docker-compose up -d

# Check status
docker-compose ps
```

### Services

| Service | Port | Description |
|---------|------|-------------|
| frontend | 3000 | Next.js application |
| backend | 8000 | FastAPI server |
| postgres | 5432 | PostgreSQL database |
| redis | 6379 | Redis cache |
| ollama | 11434 | AI models |

### Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:password@postgres:5432/forgeai

# Redis
REDIS_URL=redis://redis:6379/0

# AI
OLLAMA_URL=http://ollama:11434
DEFAULT_MODEL=qwen2.5

# Security
JWT_SECRET=your-secret-key
CORS_ORIGINS=http://localhost:3000

# Application
APP_NAME=ForgeAI
APP_URL=http://localhost:3000
```

## Production Deployment

### Using Docker

```bash
# Build images
docker-compose -f docker-compose.prod.yml build

# Start in production mode
docker-compose -f docker-compose.prod.yml up -d
```

### Manual Deployment

```bash
# Backend
cd backend
pip install -r requirements.txt
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker

# Frontend
cd frontend
npm run build
npm run start
```

## Database Migrations

```bash
# Generate migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Frontend health
curl http://localhost:3000
```

## Monitoring

Access monitoring at:
- Grafana: http://localhost:3001 (admin/admin)
- Prometheus: http://localhost:9090

## Backup

```bash
# Database backup
pg_dump -U postgres forgeai > backup.sql

# Restore
psql -U postgres forgeai < backup.sql
```

## Troubleshooting

### Common Issues

**Container won't start**
- Check logs: `docker-compose logs <service>`
- Verify ports are available

**Database connection failed**
- Ensure PostgreSQL is healthy
- Check connection string

**Ollama not responding**
- Wait for model download
- Check Ollama logs
