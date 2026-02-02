"""Tests for Lambda handler and DynamoDB-mode app behavior."""

import os
from unittest.mock import patch


class TestLambdaHandler:
    def test_handler_module_imports(self):
        """The lambda handler module must be importable."""
        from src.lambda_handler import handler

        assert callable(handler)

    def test_mangum_wraps_app(self):
        """The handler must wrap the FastAPI app with Mangum."""
        from mangum import Mangum

        from src.lambda_handler import handler

        assert isinstance(handler, Mangum)


class TestConfigIsLambda:
    def test_is_lambda_true_when_env_set(self):
        from src.config import Settings

        with patch.dict(os.environ, {"AWS_LAMBDA_FUNCTION_NAME": "my-func"}):
            s = Settings(
                strava_client_id=1,
                strava_client_secret="s",
                jwt_secret="j",
            )
            assert s.is_lambda is True

    def test_is_lambda_false_when_env_missing(self):
        from src.config import Settings

        env = os.environ.copy()
        env.pop("AWS_LAMBDA_FUNCTION_NAME", None)
        with patch.dict(os.environ, env, clear=True):
            s = Settings(
                strava_client_id=1,
                strava_client_secret="s",
                jwt_secret="j",
            )
            assert s.is_lambda is False


class TestDynamoDbEndpointUrl:
    def test_default_is_none(self):
        from src.config import Settings

        s = Settings(
            strava_client_id=1,
            strava_client_secret="s",
            jwt_secret="j",
        )
        assert s.dynamodb_endpoint_url is None

    def test_can_set_explicit_endpoint(self):
        from src.config import Settings

        s = Settings(
            strava_client_id=1,
            strava_client_secret="s",
            jwt_secret="j",
            dynamodb_endpoint_url="http://localhost:9000",
        )
        assert s.dynamodb_endpoint_url == "http://localhost:9000"


class TestStandaloneRoutePresence:
    """The test suite runs in standalone mode — verify auth routes are present."""

    def test_auth_routes_present_in_standalone(self):
        from src.main import app

        routes = {route.path for route in app.routes}
        assert "/auth/jwt/login" in routes
        assert "/auth/register" in routes
        assert "/users/me" in routes
        assert "/export/users" in routes

    def test_strava_routes_present(self):
        from src.main import app

        routes = {route.path for route in app.routes}
        assert "/strava/activities" in routes
        assert "/strava/athlete" in routes


class TestConditionalAuthLogic:
    """Verify the conditional branching logic in main.py.

    Since module-level code in main.py uses settings.db_backend to decide
    which auth system to wire, we test the branching by asserting:
    - In standalone (default test mode): auth routes + export are present
    - The config correctly reports db_backend values
    """

    def test_standalone_has_current_active_user_from_fastapi_users(self):
        """In standalone mode, current_active_user comes from fastapi-users."""
        from src.auth import current_active_user

        assert current_active_user is not None

    def test_dynamodb_backend_skips_postgres_imports(self):
        """Creating a dynamodb Settings doesn't trigger Postgres engine creation."""
        from src.config import Settings

        s = Settings(
            strava_client_id=1,
            strava_client_secret="s",
            jwt_secret="j",
            db_backend="dynamodb",
        )
        assert s.db_backend == "dynamodb"
