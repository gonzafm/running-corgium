import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from src.strava.strava_client import StravaService
from src.config import settings


class TestStravaService(unittest.TestCase):
    def setUp(self):
        self.patcher = patch("src.strava.strava_client.Client")
        self.MockClient = self.patcher.start()
        self.service = StravaService()

    def tearDown(self):
        self.patcher.stop()

    def test_get_basic_info(self):
        expected_url = "http://mock-url"
        self.service.client.authorization_url.return_value = expected_url

        url = self.service.get_basic_info()

        self.service.client.authorization_url.assert_called_once_with(
            client_id=settings.strava_client_id,
            redirect_uri=settings.strava_redirect_uri,
        )
        self.assertEqual(url, expected_url)

    def test_authenticate_and_store(self):
        session_id = "test-session-123"
        mock_code = "mock_code"
        expected_token = "mock_access_token"
        self.service.client.exchange_code_for_token.return_value = {
            "access_token": expected_token
        }

        self.service.authenticate_and_store(session_id, mock_code)

        self.service.client.exchange_code_for_token.assert_called_once_with(
            client_id=settings.strava_client_id,
            client_secret=settings.strava_client_secret,
            code=mock_code,
        )
        self.assertEqual(self.service.tokens[session_id], expected_token)

    def test_get_athlete(self):
        session_id = "test-session-123"
        self.service.tokens[session_id] = "mock_token"
        mock_athlete = {"name": "Gonzalo"}
        self.service.client.get_athlete.return_value = mock_athlete

        result = self.service.get_athlete(session_id)

        self.service.client.get_athlete.assert_called_once()
        self.assertEqual(result, mock_athlete)
        self.assertEqual(self.service.client.access_token, "mock_token")

    def test_get_athlete_no_session_raises_error(self):
        with self.assertRaises(ValueError) as context:
            self.service.get_athlete("invalid-session")

        self.assertIn("No token found", str(context.exception))

    def test_list_activities_returns_list(self):
        session_id = "test-session-123"
        self.service.tokens[session_id] = "mock_token"

        mock_activity = MagicMock()
        mock_activity.id = 12345
        mock_activity.name = "Morning Run"
        mock_activity.distance = 5000.0
        mock_activity.moving_time = timedelta(minutes=30)
        mock_activity.elapsed_time = timedelta(minutes=32)
        mock_activity.total_elevation_gain = 50.0
        mock_activity.type = "Run"
        mock_activity.start_date = datetime(2024, 1, 15, 8, 0, 0)
        mock_activity.start_date_local = datetime(2024, 1, 15, 9, 0, 0)
        mock_activity.timezone = "Europe/Madrid"

        self.service.client.get_activities.return_value = [mock_activity]

        result = self.service.list_activities(session_id)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], 12345)
        self.assertEqual(result[0]["name"], "Morning Run")
        self.assertEqual(result[0]["distance"], 5000.0)
        self.assertEqual(result[0]["moving_time"], timedelta(minutes=30))
        self.assertEqual(result[0]["type"], "Run")
        self.service.client.get_activities.assert_called_once_with(limit=10)

    def test_list_activities_no_session_raises_error(self):
        with self.assertRaises(ValueError) as context:
            self.service.list_activities("invalid-session")

        self.assertIn("No token found", str(context.exception))

    def test_list_activities_sets_token_on_client(self):
        session_id = "test-session-123"
        self.service.tokens[session_id] = "mock_token"
        self.service.client.get_activities.return_value = []

        self.service.list_activities(session_id)

        self.assertEqual(self.service.client.access_token, "mock_token")

    def test_list_activities_with_custom_limit(self):
        session_id = "test-session-123"
        self.service.tokens[session_id] = "mock_token"
        self.service.client.get_activities.return_value = []

        self.service.list_activities(session_id, limit=5)

        self.service.client.get_activities.assert_called_once_with(limit=5)


if __name__ == "__main__":
    unittest.main()
