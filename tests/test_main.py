from unittest.mock import patch

from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


@patch("src.main.strava_service")
def test_login_redirect(mock_strava_service):
    mock_url = "http://strava.com/auth"
    mock_strava_service.get_basic_info.return_value = mock_url

    response = client.get("/login/Gonzalo", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == mock_url
    mock_strava_service.get_basic_info.assert_called_once()


@patch("src.main.strava_service")
def test_authorize(mock_strava_service):
    code = "test_code"
    session_id = "test_session_id"

    response = client.get(
        f"/strava/authorize?code={code}", cookies={"session_id": session_id}
    )

    assert response.status_code == 200
    assert response.json() == {"message": code}
    mock_strava_service.authenticate_and_store.assert_called_once_with(session_id, code)


@patch("src.main.strava_service")
def test_athlete(mock_strava_service):
    mock_athlete = {"id": 123, "firstname": "Gonzalo"}
    mock_strava_service.get_athlete.return_value = mock_athlete

    response = client.get("/strava/athlete")

    assert response.status_code == 200
    assert response.json() == mock_athlete
    mock_strava_service.get_athlete.assert_called_once()
