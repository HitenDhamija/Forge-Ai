# Getting Started with ForgeAI

Welcome to ForgeAI! This guide will help you set up the development environment and run the application locally.

## Prerequisites

Before you begin, ensure you have the following installed:

| Tool | Version | Purpose |
|------|---------|---------|
| **Python** | 3.12+ | Backend runtime |
| **Node.js** | 20+ | Frontend runtime |
| **npm/yarn/pnpm** | Latest | Package management |
| **Docker** | 24+ | Containerization (optional) |
| **PostgreSQL** | 16+ | Database (or use Docker) |
| **Git** | 2.30+ | Version control |

### Checking Prerequisites

```bash
python3 --version   # Should be 3.12+
node --version      # Should be 20+
docker --version    # Should be 24+
```

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/forgeai.git
cd forgeai
```

### 2. Run Setup Script

The fastest way to get started:

```bash
./scripts/setup.sh
```

This script will:
- Verify all prerequisites are installed
- Create a Python virtual environment
- Install Python dependencies
- Install Node.js dependencies
- Create `.env` files from templates

### 3. Manual Setup (Alternative)

If you prefer manual setup:

#### Backend Setup

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install poetry
poetry config virtualenvs.create false
poetry install

# Or with pip
pip install -e ".[dev]"
```

#### Frontend Setup

```bash
# Install dependencies
npm install

# Or with yarn
yarn install

# Or with pnpm
pnpm install
```

#### Environment Variables

```bash
# Copy environment files
cp .env.example .env
cp docker/.env.example docker/.env
```

Edit `.env` with your configuration (see [Environment Variables](#environment-variables)).

## Running Development

### Option 1: Docker (Recommended)

Start the full development environment with Docker:

```bash
# Start all services
./scripts/dev.sh

# Or manually
docker compose -f docker/docker-compose.dev.yml up
```

This starts:
- **Backend**: http://localhost:8000
- **Frontend**: http://localhost:3000
- **PostgreSQL**: localhost:5432

### Option 2: Local Development

If you have PostgreSQL running locally:

```bash
# Start backend (Terminal 1)
uvicorn app.main:app --reload --port 8000

# Start frontend (Terminal 2)
npm run dev
```

### Option 3: Mixed Mode

Use Docker for the database, run apps locally:

```bash
# Start only PostgreSQL
docker compose -f docker/docker-compose.dev.yml up -d postgres

# Start backend and frontend locally
./scripts/dev.sh
```

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://user:pass@localhost:5432/forgeai` |
| `JWT_SECRET_KEY` | Secret for JWT tokens | `your-super-secret-key` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_ENV` | Environment name | `development` |
| `DEBUG` | Enable debug mode | `true` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `BACKEND_CORS_ORIGINS` | Allowed CORS origins | `["http://localhost:3000"]` |

### AI Provider Keys (Optional)

```bash
OPENAI_API_KEY=sk-your-key
ANTHROPIC_API_KEY=sk-ant-your-key
```

## First API Call

Once the backend is running, test it:

### Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "ok",
  "service": "forgeai",
  "version": "0.1.0",
  "database": {
    "status": "connected"
  }
}
```

### API Documentation

Visit the interactive API docs:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Example: Create a User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "johndoe",
    "password": "SecurePass123!",
    "full_name": "John Doe"
  }'
```

## Troubleshooting

### Common Issues

**Port already in use**
```bash
# Find process using the port
lsof -i :8000
# Kill the process
kill -9 <PID>
```

**Database connection refused**
```bash
# Ensure PostgreSQL is running
docker compose -f docker/docker-compose.dev.yml up -d postgres

# Check status
docker compose -f docker/docker-compose.dev.yml ps
```

**Module not found errors**
```bash
# Reinstall dependencies
pip install -e ".[dev]"
npm install
```

### Getting Help

- Check the [Developer Guide](DeveloperGuide.md)
- Review [Architecture Documentation](Architecture.md)
- Open an issue on GitHub

## Next Steps

1. Explore the [API Documentation](http://localhost:8000/docs)
2. Read the [Developer Guide](DeveloperGuide.md)
3. Review [Coding Standards](CodingStandards.md)
4. Check out the [Architecture](Architecture.md)

---

*Happy coding! Welcome to the ForgeAI community.*
