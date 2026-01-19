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
