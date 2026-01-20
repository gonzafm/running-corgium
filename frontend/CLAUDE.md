# CLAUDE.md - Frontend Development Rules

## Project Overview
React + Vite + TypeScript frontend for the running-corgium project. Connects to the Python/FastAPI backend for Strava integration.

## Tech Stack
- **Framework:** React 19 with TypeScript
- **Build Tool:** Vite 7
- **Package Manager:** Bun
- **Test Runner:** Vitest
- **Testing Libraries:**
  - @testing-library/react (component testing)
  - MSW (Mock Service Worker for API mocking)
- **Routing:** react-router-dom

## Development Guidelines

### Architecture
- **API Layer:** `src/api/` abstracts all backend communication
- **Components:** `src/components/` contains reusable UI components
- **Pages:** `src/pages/` contains route-level components
- **Hooks:** `src/hooks/` contains custom React hooks
- **Types:** `src/api/types.ts` defines all API response types

### Coding Standards
- Use strict TypeScript (`strict: true` in tsconfig)
- Prefer functional components with hooks
- Use named exports (not default exports) for better refactoring
- Keep components small and focused (single responsibility)
- All async operations must handle errors gracefully

### Testing Strategy
Two test categories:
1. **Unit Tests (`tests/unit/`):** Fast, isolated tests using MSW
   - Mock all network requests
   - Test components, hooks, and API client in isolation
   - Run with: `bun run test:unit`

2. **Integration Tests (`tests/integration/`):** Real backend validation
   - Require running backend on localhost:8000
   - Validate actual API contracts
   - Skip gracefully if backend unavailable
   - Run with: `bun run test:integration`

### API Communication
- Always use the `apiClient` from `src/api/client.ts`
- Never make direct fetch calls in components
- All API types must be defined in `src/api/types.ts`
- Handle loading, error, and success states explicitly

### Environment Variables
- `VITE_API_URL`: Backend URL (empty for dev proxy, full URL for production)
- `VITE_BACKEND_URL`: Used in integration tests (default: http://localhost:8000)

## Common Commands
- **Start dev server:** `bun dev` (runs on http://localhost:5173)
- **Run all tests:** `bun test`
- **Run unit tests only:** `bun run test:unit`
- **Run integration tests:** `bun run test:integration`
- **Type checking:** `bun run typecheck`
- **Lint:** `bun run lint`
- **Build:** `bun run build`

## Backend Proxy Configuration
In development, Vite proxies `/login/*` and `/strava/*` to `http://localhost:8000`.
Start the backend with: `uv run uvicorn src.main:app --reload` from project root.

## Important Notes
- Do not store OAuth tokens in localStorage (security risk)
- The `/login/:name` endpoint causes a browser redirect - handle accordingly
- Integration tests require the Python backend to be running
- MSW handlers in `tests/mocks/handlers.ts` should mirror actual API behavior
