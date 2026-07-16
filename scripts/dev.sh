#!/usr/bin/env bash
# ============================================================
# ForgeAI Development Environment Startup Script
# ============================================================
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================
# Helper Functions
# ============================================================
print_header() {
    echo ""
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}============================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Store PIDs of background processes
PIDS=()

cleanup() {
    echo ""
    print_header "Shutting Down"

    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
        fi
    done

    print_success "All services stopped"
    exit 0
}

trap cleanup SIGINT SIGTERM

# ============================================================
# Main
# ============================================================
main() {
    print_header "ForgeAI Development Environment"

    # Navigate to project root
    PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
    cd "$PROJECT_ROOT"

    # ============================================================
    # Start PostgreSQL via Docker
    # ============================================================
    print_header "Starting PostgreSQL"

    if command -v docker &> /dev/null; then
        # Check if postgres is already running
        if docker ps --format '{{.Names}}' | grep -q "forgeai-postgres-dev"; then
            print_success "PostgreSQL is already running"
        else
            print_success "Starting PostgreSQL container..."

            # Start postgres from docker-compose
            docker compose -f docker/docker-compose.dev.yml up -d postgres 2>/dev/null || \
                docker-compose -f docker/docker-compose.dev.yml up -d postgres 2>/dev/null

            # Wait for PostgreSQL to be ready
            print_success "Waiting for PostgreSQL to be ready..."
            for i in {1..30}; do
                if docker exec forgeai-postgres-dev pg_isready -U forgeai -d forgeai &>/dev/null; then
                    print_success "PostgreSQL is ready"
                    break
                fi
                if [ "$i" -eq 30 ]; then
                    print_error "PostgreSQL failed to start within 30 seconds"
                    exit 1
                fi
                sleep 1
            done
        fi
    else
        print_warning "Docker not available - PostgreSQL must be running externally"
    fi

    # ============================================================
    # Start Backend
    # ============================================================
    print_header "Starting Backend"

    # Activate virtual environment if it exists
    if [ -d "venv" ]; then
        source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null
        print_success "Activated virtual environment"
    fi

    # Install dependencies if needed
    if [ -f "pyproject.toml" ]; then
        print_success "Installing Python dependencies..."
        pip install -e ".[dev]" --quiet 2>/dev/null || true
    fi

    # Start backend server
    print_success "Starting FastAPI backend..."
    uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --reload \
        --reload-dir app \
        --log-level info \
        &
    PIDS+=($!)
    print_success "Backend started (PID: $!)"

    # ============================================================
    # Start Frontend
    # ============================================================
    print_header "Starting Frontend"

    # Install dependencies if needed
    if [ -f "package.json" ]; then
        print_success "Installing Node.js dependencies..."
        npm install --silent 2>/dev/null || true
    fi

    # Start frontend server
    print_success "Starting Next.js frontend..."
    npm run dev &
    PIDS+=($!)
    print_success "Frontend started (PID: $!)"

    # ============================================================
    # Print URLs
    # ============================================================
    print_header "Services Running"

    echo ""
    echo -e "${GREEN}All services are running!${NC}"
    echo ""
    echo -e "  ${BLUE}Backend API:      ${NC}http://localhost:8000"
    echo -e "  ${BLUE}API Documentation: ${NC}http://localhost:8000/docs"
    echo -e "  ${BLUE}ReDoc:            ${NC}http://localhost:8000/redoc"
    echo -e "  ${BLUE}Frontend:         ${NC}http://localhost:3000"
    echo ""
    echo -e "  ${YELLOW}Press Ctrl+C to stop all services${NC}"
    echo ""

    # Wait for background processes
    wait
}

# Run main function
main "$@"
