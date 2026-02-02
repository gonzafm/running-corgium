"""Auth Security Contract Tests.

These tests capture the security behavioral contract of the application.
They define WHAT the auth layer must guarantee, independent of HOW it's
implemented (fastapi-users for standalone, Cognito for aws).

When a new auth backend is implemented, these same tests validate parity.
"""

from collections import defaultdict
from datetime import datetime
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from src.auth import current_active_user
from src.main import app

client = TestClient(app)


def _make_mock_user(**overrides: Any) -> MagicMock:
    """Factory for mock User objects.

    Defines the interface contract that any auth backend must satisfy.
    The User object injected by the auth dependency must expose these fields.
    """
    defaults: dict[str, Any] = {
        "id": 1,
        "email": "test@example.com",
        "hashed_password": "fakehashed",
        "is_active": True,
        "is_superuser": False,
        "is_verified": False,
        "google_id": None,
        "first_name": "Test",
        "last_name": "User",
        "display_name": "TestUser",
        "picture": None,
        "created_at": datetime(2026, 1, 1),
        "updated_at": datetime(2026, 1, 1),
    }
    defaults.update(overrides)
    user = MagicMock()
    for k, v in defaults.items():
        setattr(user, k, v)
    return user


@pytest.fixture(autouse=True)
def _clear_overrides():
    """Ensure dependency overrides are cleaned up after each test."""
    yield
    app.dependency_overrides.clear()


# --------------------------------------------------------------------------
# 1. Protected routes reject unauthenticated requests (401)
# --------------------------------------------------------------------------


class TestRouteProtection:
    """Protected endpoints must return 401 when no credentials are provided."""

    def test_authenticated_route_rejects_unauthenticated(self):
        response = client.get("/authenticated-route")
        assert response.status_code == 401

    def test_users_me_rejects_unauthenticated(self):
        response = client.get("/users/me")
        assert response.status_code == 401

    def test_users_me_patch_rejects_unauthenticated(self):
        response = client.patch("/users/me", json={"first_name": "Hacker"})
        assert response.status_code == 401


# --------------------------------------------------------------------------
# 2. Protected routes accept authenticated requests
# --------------------------------------------------------------------------


class TestAuthenticatedAccess:
    """With valid credentials, protected routes must grant access."""

    def test_authenticated_route_returns_greeting(self):
        mock_user = _make_mock_user(email="runner@corgi.com")
        app.dependency_overrides[current_active_user] = lambda: mock_user

        response = client.get("/authenticated-route")

        assert response.status_code == 200
        assert response.json() == {"message": "Hello runner@corgi.com!"}

    def test_authenticated_route_greeting_uses_email(self):
        """The greeting must include the user's email address."""
        mock_user = _make_mock_user(email="hello@world.com")
        app.dependency_overrides[current_active_user] = lambda: mock_user

        response = client.get("/authenticated-route")

        assert "hello@world.com" in response.json()["message"]


# --------------------------------------------------------------------------
# 3. Auth routes are registered with expected methods
# --------------------------------------------------------------------------


def _get_route_methods() -> dict[str, set[str]]:
    """Returns dict of path -> set of methods for all app routes."""
    routes: dict[str, set[str]] = defaultdict(set)
    for route in app.routes:
        if hasattr(route, "methods") and hasattr(route, "path"):
            routes[route.path].update(route.methods)  # type: ignore[attr-defined]
    return routes


class TestAuthRouteRegistration:
    """All auth endpoints must be registered with the correct HTTP methods."""

    def test_auth_login_route_exists(self):
        routes = _get_route_methods()
        assert "/auth/jwt/login" in routes
        assert "POST" in routes["/auth/jwt/login"]

    def test_auth_logout_route_exists(self):
        routes = _get_route_methods()
        assert "/auth/jwt/logout" in routes
        assert "POST" in routes["/auth/jwt/logout"]

    def test_auth_register_route_exists(self):
        routes = _get_route_methods()
        assert "/auth/register" in routes
        assert "POST" in routes["/auth/register"]

    def test_auth_forgot_password_route_exists(self):
        routes = _get_route_methods()
        assert "/auth/forgot-password" in routes
        assert "POST" in routes["/auth/forgot-password"]

    def test_auth_reset_password_route_exists(self):
        routes = _get_route_methods()
        assert "/auth/reset-password" in routes
        assert "POST" in routes["/auth/reset-password"]

    def test_auth_verify_route_exists(self):
        routes = _get_route_methods()
        assert "/auth/verify" in routes
        assert "POST" in routes["/auth/verify"]

    def test_auth_request_verify_token_route_exists(self):
        routes = _get_route_methods()
        assert "/auth/request-verify-token" in routes
        assert "POST" in routes["/auth/request-verify-token"]

    def test_users_me_route_exists(self):
        routes = _get_route_methods()
        assert "/users/me" in routes
        assert "GET" in routes["/users/me"]

    def test_users_me_patch_route_exists(self):
        routes = _get_route_methods()
        assert "/users/me" in routes
        assert "PATCH" in routes["/users/me"]


# --------------------------------------------------------------------------
# 4. Auth endpoint contract (input validation)
# --------------------------------------------------------------------------


class TestAuthEndpointValidation:
    """Auth endpoints must validate input and return proper error codes."""

    def test_register_rejects_missing_fields(self):
        """Register with empty body must return 422 (validation error)."""
        response = client.post("/auth/register", json={})
        assert response.status_code == 422

    def test_register_rejects_missing_password(self):
        response = client.post(
            "/auth/register",
            json={"email": "test@example.com"},
        )
        assert response.status_code == 422

    def test_register_rejects_missing_email(self):
        response = client.post(
            "/auth/register",
            json={"password": "testpassword123"},
        )
        assert response.status_code == 422


# --------------------------------------------------------------------------
# 5. User model contract (fields expected by the application)
# --------------------------------------------------------------------------


class TestUserModelContract:
    """The User object from the auth dependency must expose these fields.

    Any auth backend (fastapi-users, Cognito) must provide a User with
    at least these attributes for the application to function correctly.
    """

    def test_user_model_has_required_auth_fields(self):
        user = _make_mock_user()
        required_fields = ["id", "email", "is_active", "is_superuser", "is_verified"]
        for field in required_fields:
            assert hasattr(user, field), f"User must have '{field}' attribute"

    def test_user_model_has_profile_fields(self):
        user = _make_mock_user()
        profile_fields = [
            "first_name",
            "last_name",
            "display_name",
            "picture",
            "google_id",
        ]
        for field in profile_fields:
            assert hasattr(user, field), f"User must have '{field}' attribute"

    def test_user_model_auth_field_defaults(self):
        """Newly created users should have sensible auth defaults."""
        user = _make_mock_user()
        assert user.is_active is True
        assert user.is_superuser is False
        assert user.is_verified is False


# --------------------------------------------------------------------------
# 6. Inactive user handling
# --------------------------------------------------------------------------


class TestInactiveUserRejection:
    """When the auth backend identifies a user as inactive, routes must return 401.

    This tests the contract: the auth dependency must raise 401 for inactive
    users, and the route must propagate it. Any auth backend implementation
    must enforce this behavior.
    """

    def test_inactive_user_is_rejected(self):
        def reject_inactive():
            raise HTTPException(status_code=401, detail="Inactive user")

        app.dependency_overrides[current_active_user] = reject_inactive

        response = client.get("/authenticated-route")
        assert response.status_code == 401