#!/usr/bin/env bash
# ============================================================
# ForgeAI Development Environment Setup Script
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

check_command() {
    if command -v "$1" &> /dev/null; then
        return 0
    else
        return 1
    fi
}

get_version() {
    "$1" --version 2>/dev/null | head -n 1 | grep -oE '[0-9]+\.[0-9]+(\.[0-9]+)?'
}

version_compare() {
    if [ "$1" = "$2" ]; then
        return 0
    fi
    local IFS=.
    local i ver1=($1) ver2=($2)
    for ((i=0; i<${#ver1[@]}; i++)); do
        if [ -z "${ver2[i]:-}" ]; then
            return 0
        fi
        if ((10#${ver1[i]} > 10#${ver2[i]})); then
            return 0
        fi
        if ((10#${ver1[i]} < 10#${ver2[i]})); then
            return 1
        fi
    done
    return 0
}

# ============================================================
# Main Setup
# ============================================================
main() {
    print_header "ForgeAI Development Environment Setup"

    # Check prerequisites
    print_header "Checking Prerequisites"

    # Check Python 3.12+
    if check_command python3; then
        PYTHON_VERSION=$(get_version python3)
        if version_compare "$PYTHON_VERSION" "3.12"; then
            print_success "Python $PYTHON_VERSION detected"
        else
            print_error "Python 3.12+ required, found $PYTHON_VERSION"
            exit 1
        fi
    elif check_command python; then
        PYTHON_VERSION=$(get_version python)
        if version_compare "$PYTHON_VERSION" "3.12"; then
            print_success "Python $PYTHON_VERSION detected"
        else
            print_error "Python 3.12+ required, found $PYTHON_VERSION"
            exit 1
        fi
    else
        print_error "Python is not installed. Please install Python 3.12+"
        exit 1
    fi

    # Check Node.js 20+
    if check_command node; then
        NODE_VERSION=$(get_version node)
        if version_compare "$NODE_VERSION" "20"; then
            print_success "Node.js $NODE_VERSION detected"
        else
            print_error "Node.js 20+ required, found $NODE_VERSION"
            exit 1
        fi
    else
        print_error "Node.js is not installed. Please install Node.js 20+"
        exit 1
    fi

    # Check npm
    if check_command npm; then
        NPM_VERSION=$(get_version npm)
        print_success "npm $NPM_VERSION detected"
    else
        print_error "npm is not installed"
        exit 1
    fi

    # Check Docker (optional)
    if check_command docker; then
        DOCKER_VERSION=$(get_version docker)
        print_success "Docker $DOCKER_VERSION detected"
        DOCKER_AVAILABLE=true
    else
        print_warning "Docker not found - Docker features will be unavailable"
        DOCKER_AVAILABLE=false
    fi

    # Check Docker Compose
    if check_command docker-compose || docker compose version &> /dev/null 2>&1; then
        print_success "Docker Compose detected"
    else
        print_warning "Docker Compose not found"
    fi

    # Navigate to project root
    PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
    cd "$PROJECT_ROOT"

    print_header "Setting Up Backend"

    # Create virtual environment
    if [ ! -d "venv" ]; then
        print_success "Creating Python virtual environment..."
        python3 -m venv venv 2>/dev/null || python -m venv venv
    else
        print_success "Python virtual environment already exists"
    fi

    # Activate virtual environment
    source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null

    # Upgrade pip
    print_success "Upgrading pip..."
    pip install --upgrade pip --quiet

    # Install Poetry
    if ! check_command poetry; then
        print_success "Installing Poetry..."
        pip install poetry --quiet
    else
        print_success "Poetry already installed"
    fi

    # Install Python dependencies
    print_success "Installing Python dependencies..."
    poetry config virtualenvs.create false
    poetry install --no-interaction 2>/dev/null || pip install -e ".[dev]" --quiet

    print_header "Setting Up Frontend"

    # Install Node.js dependencies
    print_success "Installing Node.js dependencies..."
    if [ -f "package-lock.json" ]; then
        npm ci --silent
    elif [ -f "yarn.lock" ]; then
        yarn install --frozen-lockfile --silent
    elif [ -f "pnpm-lock.yaml" ]; then
        pnpm install --frozen-lockfile --silent
    else
        npm install --silent
    fi

    print_header "Configuring Environment"

    # Copy root .env.example to .env if not exists
    if [ ! -f ".env" ] && [ -f ".env.example" ]; then
        cp .env.example .env
        print_success "Created root .env from .env.example"
    else
        print_success "Root .env already exists"
    fi

    # Copy docker .env.example to .env if not exists
    if [ ! -d "docker" ]; then
        mkdir -p docker
    fi
    if [ ! -f "docker/.env" ] && [ -f "docker/.env.example" ]; then
        cp docker/.env.example docker/.env
        print_success "Created docker/.env from docker/.env.example"
    else
        print_success "Docker .env already exists"
    fi

    print_header "Setup Complete!"

    echo ""
    echo -e "${GREEN}🎉 ForgeAI development environment has been set up successfully!${NC}"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo ""
    echo "  1. Start the development environment:"
    echo "     ./scripts/dev.sh"
    echo ""
    echo "  2. Access the services:"
    echo "     - Backend API:  http://localhost:8000"
    echo "     - Frontend:     http://localhost:3000"
    echo "     - API Docs:     http://localhost:8000/docs"
    echo ""
    echo "  3. Stop the development environment:"
    echo "     ./scripts/stop.sh"
    echo ""
    echo "  4. Run tests:"
    echo "     pytest tests/"
    echo ""
    echo -e "${BLUE}Happy coding! 🚀${NC}"
    echo ""
}

# Run main function
main "$@"
