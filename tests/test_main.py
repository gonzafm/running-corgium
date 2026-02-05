from unittest.mock import patch, AsyncMock

from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_app_startup_registers_auth_routes():
    routes = {route.path for route in app.routes}
    assert "/auth/jwt/login" in routes
    assert "/auth/register" in routes
    assert "/auth/forgot-password" in routes
    assert "/auth/reset-password" in routes
    assert "/auth/request-verify-token" in routes
    assert "/auth/verify" in routes
    assert "/users/me" in routes
    assert "/authenticated-route" in routes


def test_authenticated_route_requires_auth():
    response = client.get("/authenticated-route")
    assert response.status_code == 401


def test_login_redirect():
    mock_url = "http://strava.com/auth"
    with patch.object(
        app.state.strava_service, "get_basic_info", return_value=mock_url
    ) as mock_get:
        response = client.get("/login/Gonzalo", follow_redirects=False)

        assert response.status_code == 307
        assert response.headers["location"] == mock_url
        mock_get.assert_called_once()


def test_authorize():
    code = "test_code"
    session_id = "test_session_id"
    with patch.object(
        app.state.strava_service, "authenticate_and_store", new_callable=AsyncMock
    ) as mock_auth:
        client.cookies.set("session_id", session_id)
        response = client.get(f"/strava/authorize?code={code}", follow_redirects=False)
        client.cookies.clear()

        assert response.status_code == 307
        assert response.headers["location"] == "/dashboard"
        mock_auth.assert_called_once_with(session_id, code)


def test_athlete():
    mock_athlete = {"id": 123, "firstname": "Gonzalo"}
    session_id = "test_session_id"
    with patch.object(
        app.state.strava_service,
        "get_athlete",
        new_callable=AsyncMock,
        return_value=mock_athlete,
    ) as mock_get:
        client.cookies.set("session_id", session_id)
        response = client.get("/strava/athlete")
        client.cookies.clear()

        assert response.status_code == 200
        assert response.json() == mock_athlete
        mock_get.assert_called_once_with(session_id)


def test_activities():
    mock_activities = [{"id": 1, "name": "Morning Run"}, {"id": 2, "name": "Evening Walk"}]
    session_id = "test_session_id"
    with patch.object(
        app.state.strava_service,
        "list_activities",
        new_callable=AsyncMock,
        return_value=mock_activities,
    ) as mock_list:
        client.cookies.set("session_id", session_id)
        response = client.get("/strava/activities")
        client.cookies.clear()

        assert response.status_code == 200
        assert response.json() == mock_activities
        mock_list.assert_called_once_with(session_id)
