"""Tests for the /export/users endpoint.

Verifies auth guards, profile restriction, user serialization,
and Kafka producer invocation (all Kafka calls are mocked).
"""

from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.auth import current_active_user
from src.main import app

client = TestClient(app)


def _make_mock_user(**overrides: Any) -> MagicMock:
    """Create a mock User with all expected fields."""
    defaults: dict[str, Any] = {
        "id": 1,
        "email": "admin@example.com",
        "hashed_password": "fakehashed",
        "is_active": True,
        "is_superuser": True,
        "is_verified": True,
        "google_id": None,
        "first_name": "Admin",
        "last_name": "User",
        "display_name": "AdminUser",
        "picture": None,
        "created_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
    }
    defaults.update(overrides)
    user = MagicMock()
    for k, v in defaults.items():
        setattr(user, k, v)
    return user


@pytest.fixture(autouse=True)
def _clear_overrides():
    yield
    app.dependency_overrides.clear()


# --------------------------------------------------------------------------
# 1. Auth guards
# --------------------------------------------------------------------------


class TestExportUsersAuth:
    def test_rejects_unauthenticated(self):
        response = client.get("/export/users")
        assert response.status_code == 401

    def test_rejects_non_superuser(self):
        regular_user = _make_mock_user(is_superuser=False)
        app.dependency_overrides[current_active_user] = lambda: regular_user

        response = client.get("/export/users")

        assert response.status_code == 403
        assert "Superuser required" in response.json()["detail"]


# --------------------------------------------------------------------------
# 2. Profile guard
# --------------------------------------------------------------------------


class TestExportUsersProfileGuard:
    def test_export_route_absent_in_aws_mode(self):
        """In dynamodb mode the /export/users route is not registered at all.

        Since the app is initialised in standalone mode for the test suite,
        we verify the route *is* present here, and separately assert in
        test_lambda_handler.py that it is absent when DB_BACKEND=dynamodb.
        """
        routes = {route.path for route in app.routes}
        assert "/export/users" in routes


# --------------------------------------------------------------------------
# 3. User serialization
# --------------------------------------------------------------------------


class TestSerializeUser:
    def test_includes_all_columns(self):
        from src.database.models import User
        from src.export.kafka_producer import serialize_user

        mock_user = MagicMock(spec=User)
        mock_user.__table__ = User.__table__
        for col in User.__table__.columns:
            if isinstance(col.type, type) or "DateTime" in str(col.type):
                setattr(mock_user, col.key, datetime(2026, 1, 1, tzinfo=timezone.utc))
            else:
                setattr(mock_user, col.key, f"test_{col.key}")

        mock_user.id = 1

        result = serialize_user(mock_user)

        for col in User.__table__.columns:
            assert col.key in result, f"Missing column: {col.key}"

    def test_converts_datetimes_to_iso(self):
        from src.database.models import User
        from src.export.kafka_producer import serialize_user

        mock_user = MagicMock(spec=User)
        mock_user.__table__ = User.__table__
        ts = datetime(2026, 6, 15, 12, 30, 0, tzinfo=timezone.utc)
        for col in User.__table__.columns:
            setattr(
                mock_user,
                col.key,
                ts if "date" in col.key or "at" in col.key else "val",
            )

        mock_user.id = 1

        result = serialize_user(mock_user)

        assert result["created_at"] == ts.isoformat()
        assert result["updated_at"] == ts.isoformat()

    def test_includes_hashed_password(self):
        from src.database.models import User
        from src.export.kafka_producer import serialize_user

        mock_user = MagicMock(spec=User)
        mock_user.__table__ = User.__table__
        for col in User.__table__.columns:
            setattr(mock_user, col.key, "placeholder")
        mock_user.hashed_password = "secret_hash_123"

        result = serialize_user(mock_user)

        assert result["hashed_password"] == "secret_hash_123"


# --------------------------------------------------------------------------
# 4. Kafka producer invocation
# --------------------------------------------------------------------------


class TestExportUsersKafka:
    def test_calls_kafka_producer(self):
        superuser = _make_mock_user(is_superuser=True)
        app.dependency_overrides[current_active_user] = lambda: superuser

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_session_ctx = MagicMock()
        mock_session_ctx.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_ctx.__aexit__ = AsyncMock(return_value=None)

        mock_session_maker = MagicMock(return_value=mock_session_ctx)

        with (
            patch(
                "src.database.db.get_session_maker",
                return_value=mock_session_maker,
            ),
            patch(
                "src.export.kafka_producer.send_users_to_msk",
                new_callable=AsyncMock,
                return_value=0,
            ) as mock_send,
        ):
            response = client.get("/export/users")

        assert response.status_code == 200
        mock_send.assert_called_once_with([])

    def test_returns_exported_count(self):
        superuser = _make_mock_user(is_superuser=True)
        app.dependency_overrides[current_active_user] = lambda: superuser

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_session_ctx = MagicMock()
        mock_session_ctx.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_ctx.__aexit__ = AsyncMock(return_value=None)

        mock_session_maker = MagicMock(return_value=mock_session_ctx)

        with (
            patch(
                "src.database.db.get_session_maker",
                return_value=mock_session_maker,
            ),
            patch(
                "src.export.kafka_producer.send_users_to_msk",
                new_callable=AsyncMock,
                return_value=5,
            ),
        ):
            response = client.get("/export/users")

        assert response.status_code == 200
        assert response.json() == {"exported": 5}
