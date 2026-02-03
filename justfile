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

# Run with Postgres backend (backend + frontend)
dev-standalone:
    @echo "Starting with Postgres backend..."
    @echo "Backend: http://localhost:8000"
    @echo "Frontend: http://localhost:5173"
    @echo ""
    just _dev-backend "standalone" & just dev-frontend & wait

# Run with DynamoDB backend (backend + frontend)
dev-aws:
    @echo "Starting with DynamoDB backend..."
    @echo "Backend: http://localhost:8000"
    @echo "Frontend: http://localhost:5173"
    @echo ""
    just _dev-backend "aws" & just dev-frontend & wait

# Run FastAPI server with the given backend
_dev-backend backend:
    DB_BACKEND={{backend}} uv run uvicorn src.main:app --reload --port 8000

# Run Vite dev server (port 5173)
dev-frontend:
    cd frontend && bun dev

# ============================================================================
# Lambda Deployment
# ============================================================================

ACCOUNT_ID := "170744924235"
AWS_REGION := "us-east-2"
ECR_REPO   := ACCOUNT_ID + ".dkr.ecr." + AWS_REGION + ".amazoncognito.com/running-corgium"
ECR_IMAGE  := ACCOUNT_ID + ".dkr.ecr." + AWS_REGION + ".amazonaws.com/running-corgium:latest"
LAMBDA_FN  := "running-corgium"

# Build frontend with Cognito config, Docker image, push to ECR, and update Lambda
deploy-lambda: _lambda-build-frontend _lambda-docker-push _lambda-update
    @echo "Lambda deploy complete!"

# Build frontend with Cognito env vars
_lambda-build-frontend:
    @echo "Building frontend (cognito mode)..."
    cd frontend && \
      VITE_AUTH_MODE=cognito \
      VITE_COGNITO_DOMAIN=running-corgium.auth.us-east-2.amazoncognito.com \
      VITE_COGNITO_CLIENT_ID=5a7mim2os4br7vg4ikv2tejsr \
      VITE_COGNITO_REDIRECT_URI=https://5en3exrtx6.execute-api.us-east-2.amazonaws.com/auth/callback \
      bun run build
    @echo "Verifying authMode..."
    grep -o 'authMode:"[^"]*"' frontend/dist/assets/index-*.js

# Build Docker image and push to ECR
_lambda-docker-push:
    @echo "Logging in to ECR..."
    aws ecr get-login-password --region {{AWS_REGION}} | docker login --username AWS --password-stdin {{ACCOUNT_ID}}.dkr.ecr.{{AWS_REGION}}.amazonaws.com
    @echo "Building Docker image..."
    docker build --platform linux/amd64 --provenance=false --no-cache -f Dockerfile.lambda -t running-corgium:latest .
    @echo "Pushing to ECR..."
    docker tag running-corgium:latest {{ECR_IMAGE}}
    docker push {{ECR_IMAGE}}

# Update Lambda function code
_lambda-update:
    @echo "Updating Lambda function..."
    aws lambda update-function-code --function-name {{LAMBDA_FN}} --image-uri {{ECR_IMAGE}} --region {{AWS_REGION}}
    @echo "Waiting for update to complete..."
    aws lambda wait function-updated --function-name {{LAMBDA_FN}} --region {{AWS_REGION}}
    @echo "Lambda function updated successfully."

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
