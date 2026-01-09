# GEMINI.md - Project Context & Instructions

## Project Overview
**running-corgium** is a Python-based service that integrates Strava data via FastAPI and gRPC. It serves as a bridge between fitness activities and other internal services.

## Tech Stack
- **Language:** Python 3.14+ (using `uv` for package management)
- **Web Framework:** FastAPI (for REST/HTTP)
- **Communication:** gRPC (Protobuf definitions in `/protos`) and REST
- **Third-party APIs:** Strava API via `stravalib`
- **Quality Tools:** Ruff (linting), Mypy (types), Pytest (testing)

## Development Guidelines

### Architecture
- **API Layer:** `src/main.py` handles REST endpoints.
- **Service Layer:** `src/grpc_server.py` implements the gRPC service.
- **Client Layer:** `src/strava/` contains logic for interacting with external APIs.
- **Generated Code:** Do not manually edit files in `src/generated/`. These are updated via `protoc`.

### Coding Standards
- Use strict type hinting everywhere.
- Prefer `async/await` for all I/O bound operations (FastAPI and Strava client).
- Follow PEP 8 via Ruff configuration.

### Testing
- All new features must have corresponding tests in `/tests`.
- Mock external network calls to Strava using `pytest-mock`.
- Run tests using `pytest`.

## Common Commands
- **Run FastAPI server:** `uv run uvicorn src.main:app --reload`
- **Run gRPC server:** `uv run python src/grpc_server.py`
- **Run Tests:** `uv run pytest`
- **Linting:** `uv run ruff check .`
- **Type Checking:** `uv run mypy .`
- **Regenerate gRPC:** 
  ```bash
  python -m grpc_tools.protoc -I./protos --python_out=src/generated --grpc_python_out=src/generated ./protos/helloworld.proto
  ```
  *(Note: Adjust the output path if necessary to match import structures)*

## Contextual Priorities
- Focus on hybrid mode with gRPC and REST.
- Ensure Strava OAuth tokens are handled securely (do not log them).
