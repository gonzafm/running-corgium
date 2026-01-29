# Running Corgium - Local Development Commands
# Usage: just <recipe>

# Default recipe - show help
default:
    @just --list

# ============================================================================
# Installation
# ============================================================================

# Install all dependencies (backend + frontend)
install: install-backend install-frontend
    @echo "All dependencies installed!"

# Install Python dependencies
install-backend:
    @echo "Installing Python dependencies..."
    uv sync --locked --all-extras --dev

# Install frontend dependencies
install-frontend:
    @echo "Installing frontend dependencies..."
    cd frontend && bun install

# ============================================================================
# Build
# ============================================================================

# Build both frontend and backend
build: build-backend build-frontend
    @echo "Build complete!"

# Type check Python code
build-backend:
    @echo "Type checking Python..."
    uv run mypy .

# Build frontend for production
build-frontend:
    @echo "Building frontend..."
    cd frontend && bun run build

# ============================================================================
# Test
# ============================================================================

# Run all tests
test: test-backend test-frontend
    @echo "All tests complete!"

# Run Python tests
test-backend:
    @echo "Running Python tests..."
    uv run pytest tests

# Run Python tests with coverage
test-cov:
    @echo "Running Python tests with coverage..."
    uv run pytest tests --cov=src --cov-report=term-missing --cov-report=html

# Run frontend tests
test-frontend:
    @echo "Running frontend tests..."
    cd frontend && bun run test

# ============================================================================
# Lint
# ============================================================================

# Lint all code
lint: lint-backend lint-frontend
    @echo "Lint complete!"

# Lint Python code
lint-backend:
    @echo "Linting Python..."
    uv run ruff check .

# Lint frontend code
lint-frontend:
    @echo "Linting frontend..."
    cd frontend && bun run lint

# Run ruff + bandit security scan
lint-security:
    @echo "Running ruff..."
    uv run ruff check .
    @echo "Running bandit security scan..."
    uv run bandit -r src/ -q

# ============================================================================
# Development Servers
# ============================================================================

# Run both servers (backend + frontend)
dev:
    @echo "Starting both servers..."
    @echo "Backend: http://localhost:8000"
    @echo "Frontend: http://localhost:5173"
    @echo ""
    just dev-backend & just dev-frontend & wait

# Run FastAPI server (port 8000)
dev-backend:
    uv run uvicorn src.main:app --reload --port 8000

# Run Vite dev server (port 5173)
dev-frontend:
    cd frontend && bun dev

# ============================================================================
# Cleanup
# ============================================================================

# Remove build artifacts
clean:
    @echo "Cleaning build artifacts..."
    rm -rf frontend/dist
    rm -rf frontend/coverage
    rm -rf .pytest_cache
    rm -rf .mypy_cache
    rm -rf .ruff_cache
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    @echo "Clean complete!"
