# CLAUDE.md - Project Context & Instructions

## Project Overview
**running-corgium** is a Python-based service that integrates Strava data via FastAPI and gRPC. It serves as a bridge between fitness activities and other internal services.

## Tech Stack
- **Language:** Python 3.14+ (using `uv` for package management)
- **Web Framework:** FastAPI (for REST/HTTP)
- **Communication:** gRPC (Protobuf definitions in `/protos`) and REST
- **Third-party APIs:** Strava API via `stravalib`
- **Quality Tools:** Ruff (linting), Mypy (types), Pytest (testing)
- **Database:** Postgres via asyncpg

## Functional Requirements

- /strava/activities: should return a list of all activities
- The guiding principle is to call strava API as little as possible. For that purporse replicating in DB is desirable.
- Once a date from activities is retrieved, it should be persisted in DB. Only when new dates are requested, those dates should be retrieved from strava API

## Development Guidelines

### Architecture
- **API Layer:** `src/main.py` handles REST endpoints.
- **Client Layer:** `src/strava/` contains logic for interacting with external APIs.
- **Generated Code:** Do not manually edit files in `src/generated/`. These are updated via `protoc`.
- **Database:** Module `src/database`. Use `asyncpg` for all database operations.

### Coding Standards
- Use strict type hinting everywhere.
- Prefer `async/await` for all I/O bound operations (FastAPI and Strava client).
- Follow PEP 8 via Ruff configuration.
- Follow best practices from Effective Python.

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


## Contextual Priorities
- Focus on REST.
- Ensure Strava OAuth tokens are handled securely (do not log them).
- Do not commit code. Only add files via `git add -A`.