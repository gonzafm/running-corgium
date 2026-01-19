# Previous Issues

## 2026-01-19: `just build` failing with mypy type errors

### Symptoms
Running `just build` failed during the `build-backend` step with multiple mypy errors:

```
src/generated/helloworld_pb2.pyi:1: error: Library stubs not installed for "google.protobuf"
src/generated/helloworld_pb2_grpc.py:4: error: Library stubs not installed for "grpc"
src/grpc_server.py:6: error: Cannot find implementation or library stub for module named "generated"
src/config.py:13: error: Missing named argument "strava_client_id" for "Settings"
src/strava/strava_client.py:8: error: Need type annotation for "tokens"
src/strava/strava_client.py:24: error: "None" has no attribute "exchange_code_for_token"
```

### Root Causes

1. **Missing type stubs**: The project was missing type stub packages for protobuf and gRPC libraries
2. **Incorrect import path**: `src/grpc_server.py` used `from generated import ...` instead of `from src.generated import ...`
3. **Missing type annotations**: `src/strava/strava_client.py` had untyped class variables
4. **Missing mypy pydantic plugin**: Mypy didn't understand pydantic-settings' environment variable loading

### Fixes Applied

**1. Added type stub packages to dev dependencies** (`pyproject.toml`):
```toml
[dependency-groups]
dev = [
    "grpc-stubs>=1.53.0",
    "types-protobuf>=5.29.0",
    # ... other deps
]
```

**2. Fixed import path** (`src/grpc_server.py`):
```python
# Before
from generated import helloworld_pb2

# After
from src.generated import helloworld_pb2
```

**3. Added type annotation** (`src/strava/strava_client.py`):
```python
# Before
class StravaService:
    client = None
    tokens = dict()

# After
class StravaService:
    tokens: dict[str, str] = {}
```

**4. Added mypy configuration with pydantic plugin** (`pyproject.toml`):
```toml
[tool.mypy]
plugins = ["pydantic.mypy"]
python_version = "3.14"
strict = false

[tool.pydantic-mypy]
init_forbid_extra = true
init_typed = true
warn_required_dynamic_aliases = true
```

### Verification
After applying fixes, run `just build` to verify:
```
$ just build
Type checking Python...
Success: no issues found in 12 source files
Building frontend...
Build complete!
```

---

## 2026-01-19: Implemented Strava OAuth Callback Flow with Athlete Page Redirect

### Context
The frontend receives OAuth callbacks from Strava at `http://localhost:5173/auth/callback`. The implementation ensures:
1. Frontend correctly receives the callback with authorization code
2. Frontend passes the code to the backend
3. Frontend logs the incoming message from backend response
4. Frontend redirects to the dedicated Athlete page

### OAuth Flow Overview
```
Strava OAuth Server
        │
        │ Redirects with ?code=XXX
        ▼
Frontend: /auth/callback (OAuthCallback component)
        │
        │ GET /strava/authorize?code=XXX
        ▼
Backend: Logs "Strava called back with code: XXX"
        │ Returns: {"message": code}
        ▼
Frontend: Logs "Strava authorization response: XXX"
        │
        │ After 1.5s delay
        ▼
Frontend: Redirects to /athlete (AthletePage)
```

### Files Created/Modified

**New file:** `frontend/src/pages/AthletePage.tsx`
- Dedicated page for displaying athlete profile after OAuth

**Modified:** `frontend/src/App.tsx`
- Added `/athlete` route pointing to `AthletePage`

**Modified:** `frontend/src/components/OAuthCallback.tsx`
- Added logging of backend response message
- Changed redirect from `/dashboard` to `/athlete`

**New file:** `frontend/tests/unit/components/OAuthCallback.test.tsx`
- Comprehensive test coverage for OAuth callback flow

### Implementation Details

**OAuthCallback changes:**
```typescript
const authorize = async () => {
  try {
    const response = await stravaApi.authorize(code);
    console.log('Strava authorization response:', response.message);  // Log incoming message
    setStatus('success');
    setTimeout(() => navigate('/athlete'), 1500);  // Redirect to Athlete page
  } catch (err) {
    // error handling
  }
};
```

**New route added:**
```typescript
<Route path="/athlete" element={<AthletePage />} />
```

### Test Cases Covered
1. **Loading state**: Displays "Authorizing..." when receiving callback
2. **Success flow**: Passes code to backend, logs response, redirects to athlete page
3. **Missing code error**: Shows error when no authorization code provided
4. **URL param extraction**: Correctly extracts code from URL search params
5. **Error handling**: Gracefully handles backend authorization errors
6. **Full flow**: End-to-end test of receive → log → redirect to athlete

### Running the Tests
```bash
# Run only OAuth callback tests
cd frontend && bun run test:unit -- --run tests/unit/components/OAuthCallback.test.tsx

# Run all unit tests
cd frontend && bun run test:unit
```

### Verification
```
$ bun run test:unit
 ✓ tests/unit/components/OAuthCallback.test.tsx (6 tests) 3093ms
   ✓ should display loading state when receiving callback from Strava
   ✓ should pass authorization code to backend, log response, and redirect to athlete page on success
   ✓ should handle missing authorization code with error state
   ✓ should extract code from URL search params correctly
   ✓ should handle backend authorization error gracefully
   ✓ should complete full OAuth callback flow: receive -> log -> redirect to athlete
```

---

## 2026-01-19: Fixed OAuth Callback Not Redirecting to Athlete Page

### Problem
After Strava OAuth callback to `http://localhost:5173/auth/callback?code=XXX`, the user was not being redirected to the athlete page.

### Root Causes
1. **React Strict Mode double execution**: In development, React's strict mode runs effects twice. Since Strava authorization codes are single-use, the second execution would fail.
2. **Missing error handling in backend**: The stravalib `exchange_code_for_token` call could throw exceptions that weren't being caught properly.

### Fixes Applied

**Frontend (`src/components/OAuthCallback.tsx`):**
- Added `useRef` guard to prevent double execution of authorization
- Added console logging for debugging

```typescript
const hasAuthorized = useRef(false);

useEffect(() => {
  if (hasAuthorized.current) {
    return;  // Prevent double execution
  }
  // ... rest of effect
  hasAuthorized.current = true;
  // ... authorize
}, [searchParams, navigate]);
```

**Backend (`src/main.py`):**
- Added try/catch around `authenticate_and_store` call
- Returns proper HTTP 400 error with details on failure

```python
@app.get("/strava/authorize")
async def authorize(code: str):
    try:
        strava_service.authenticate_and_store(code)
        return {"message": code}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### Debugging Tips
Check browser console for these log messages:
- `Authorizing with code: XXX` - confirms code was extracted
- `Strava authorization response: XXX` - confirms backend call succeeded
- `Authorization failed: XXX` - shows error details if failed

---

## 2026-01-19: Fixed Vite Proxy Intercepting OAuth Callback Route

### Problem
After Strava OAuth, the callback was being intercepted by Vite's proxy and forwarded directly to the backend, bypassing the React frontend entirely. No frontend logs were appearing.

### Root Cause
The Vite proxy configuration proxied ALL `/strava/*` requests to the backend:
```javascript
proxy: {
  '/strava': {
    target: 'http://localhost:8000',
    changeOrigin: true,
  },
}
```

This meant when Strava redirected to `http://localhost:5173/auth/callback?code=XXX`, Vite forwarded it to the backend instead of serving the React app.

### Fix
Changed the frontend callback route from `/strava/authorize` to `/auth/callback` to avoid the proxy:

**Files changed:**
- `frontend/src/App.tsx`: Route changed to `/auth/callback`
- `src/config.py`: Default redirect_uri updated
- `.env`: `STRAVA_REDIRECT_URI=http://localhost:5173/auth/callback`

**New OAuth flow:**
```
Strava OAuth Server
        │
        │ Redirects to http://localhost:5173/auth/callback?code=XXX
        ▼
Frontend: /auth/callback (OAuthCallback component)
        │
        │ fetch /strava/authorize?code=XXX (proxied to backend)
        ▼
Backend: Exchanges code for token
        │
        ▼
Frontend: Redirects to /athlete
```

### Important
After this change, **restart both servers**:
```bash
# Terminal 1 - Backend
uv run uvicorn src.main:app --reload

# Terminal 2 - Frontend
cd frontend && bun dev
```
