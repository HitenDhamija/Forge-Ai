#!/usr/bin/env bash
# ============================================================
# ForgeAI Development Environment Stop Script
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

# ============================================================
# Main
# ============================================================
main() {
    print_header "ForgeAI Development Environment Shutdown"

    # Navigate to project root
    PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
    cd "$PROJECT_ROOT"

    # ============================================================
    # Stop Backend
    # ============================================================
    print_header "Stopping Backend"

    if pgrep -f "uvicorn app.main:app" > /dev/null 2>&1; then
        pkill -f "uvicorn app.main:app"
        print_success "Backend stopped"
    else
        print_warning "Backend was not running"
    fi

    # ============================================================
    # Stop Frontend
    # ============================================================
    print_header "Stopping Frontend"

    # Stop npm/node processes
    if pgrep -f "next dev" > /dev/null 2>&1; then
        pkill -f "next dev"
        print_success "Frontend (Next.js) stopped"
    else
        print_warning "Frontend was not running"
    fi

    # Stop any node processes on port 3000
    if lsof -ti:3000 > /dev/null 2>&1; then
        lsof -ti:3000 | xargs kill -9 2>/dev/null || true
        print_success "Cleared processes on port 3000"
    fi

    # ============================================================
    # Stop Docker Services
    # ============================================================
    print_header "Stopping Docker Services"

    if command -v docker &> /dev/null; then
        # Stop development containers
        docker compose -f docker/docker-compose.dev.yml down 2>/dev/null || \
            docker-compose -f docker/docker-compose.dev.yml down 2>/dev/null || true

        print_success "Docker Compose services stopped"

        # Optionally remove containers
        if [ "${1:-}" = "--clean" ]; then
            print_warning "Removing containers and volumes..."
            docker compose -f docker/docker-compose.dev.yml down -v 2>/dev/null || \
                docker-compose -f docker/docker-compose.dev.yml down -v 2>/dev/null || true
            print_success "Docker resources cleaned"
        fi
    else
        print_warning "Docker not available - skipping container cleanup"
    fi

    # ============================================================
    # Summary
    # ============================================================
    print_header "Shutdown Complete"

    echo ""
    echo -e "${GREEN}All services have been stopped.${NC}"
    echo ""
    echo -e "  ${YELLOW}Tip:${NC} Run ${BLUE}./scripts/dev.sh${NC} to start again"
    echo ""
}

# Run main function
main "$@"
