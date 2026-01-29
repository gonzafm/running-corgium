import unittest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone
from src.strava.strava_client import StravaService
from src.config import settings


class TestStravaService(unittest.IsolatedAsyncioTestCase):
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

    async def test_authenticate_and_store(self):
        session_id = "test-session-123"
        mock_code = "mock_code"
        expected_token = "mock_access_token"
        self.service.client.exchange_code_for_token.return_value = {
            "access_token": expected_token
        }

        await self.service.authenticate_and_store(session_id, mock_code)

        self.service.client.exchange_code_for_token.assert_called_once_with(
            client_id=settings.strava_client_id,
            client_secret=settings.strava_client_secret,
            code=mock_code,
        )
        self.assertEqual(self.service.tokens[session_id], expected_token)

    async def test_get_athlete(self):
        session_id = "test-session-123"
        self.service.tokens[session_id] = "mock_token"
        mock_athlete = {"name": "Gonzalo"}
        self.service.client.get_athlete.return_value = mock_athlete

        result = await self.service.get_athlete(session_id)

        self.service.client.get_athlete.assert_called_once()
        self.assertEqual(result, mock_athlete)
        self.assertEqual(self.service.client.access_token, "mock_token")

    async def test_get_athlete_no_session_raises_error(self):
        with self.assertRaises(ValueError) as context:
            await self.service.get_athlete("invalid-session")

        self.assertIn("No token found", str(context.exception))

    async def test_list_activities_returns_all_from_database(self):
        session_id = "test-session-123"
        self.service.tokens[session_id] = "mock_token"

        # Create mock SummaryActivity objects
        mock_activity1 = MagicMock()
        mock_activity1.id = 111
        mock_activity1.name = "Morning Run"
        mock_activity2 = MagicMock()
        mock_activity2.id = 222
        mock_activity2.name = "Evening Walk"

        self.service.postgres_service = MagicMock()
        self.service.postgres_service.get_last_sync_date.return_value = datetime(
            2024, 1, 10, tzinfo=timezone.utc
        )
        self.service.postgres_service.is_activity_synced.return_value = True
        self.service.postgres_service.get_activities = AsyncMock(
            return_value=[mock_activity1, mock_activity2]
        )

        # No new activities from Strava
        self.service.client.get_activities.return_value = []

        result = await self.service.list_activities(session_id)

        # Should return activities from database
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].name, "Morning Run")
        self.assertEqual(result[1].name, "Evening Walk")
        self.service.postgres_service.get_activities.assert_called_once_with(limit=100)

    async def test_list_activities_syncs_new_activities_first(self):
        session_id = "test-session-123"
        self.service.tokens[session_id] = "mock_token"
        last_sync = datetime(2024, 1, 10, 0, 0, 0, tzinfo=timezone.utc)

        self.service.postgres_service = MagicMock()
        self.service.postgres_service.get_last_sync_date.return_value = last_sync
        self.service.postgres_service.is_activity_synced.return_value = False
        self.service.postgres_service.insert_activity = AsyncMock(return_value=True)
        self.service.postgres_service.get_activities = AsyncMock(return_value=[])

        mock_activity = MagicMock()
        mock_activity.id = 12345
        mock_activity.name = "Morning Run"
        self.service.client.get_activities.return_value = [mock_activity]

        await self.service.list_activities(session_id)

        # Should fetch from Strava using after parameter
        self.service.client.get_activities.assert_called_once_with(after=last_sync)
        # Should insert the new activity
        self.service.postgres_service.insert_activity.assert_called_once_with(
            mock_activity
        )

    async def test_list_activities_skips_already_synced(self):
        session_id = "test-session-123"
        self.service.tokens[session_id] = "mock_token"

        self.service.postgres_service = MagicMock()
        self.service.postgres_service.get_last_sync_date.return_value = None
        self.service.postgres_service.is_activity_synced.return_value = True
        self.service.postgres_service.insert_activity = AsyncMock()
        self.service.postgres_service.get_activities = AsyncMock(return_value=[])

        mock_activity = MagicMock()
        mock_activity.id = 12345
        mock_activity.name = "Already Synced Run"
        self.service.client.get_activities.return_value = [mock_activity]

        await self.service.list_activities(session_id)

        # Should not insert already synced activities
        self.service.postgres_service.insert_activity.assert_not_called()

    async def test_list_activities_no_sync_date_fetches_recent(self):
        session_id = "test-session-123"
        self.service.tokens[session_id] = "mock_token"

        self.service.postgres_service = MagicMock()
        self.service.postgres_service.get_last_sync_date.return_value = None
        self.service.postgres_service.is_activity_synced.return_value = False
        self.service.postgres_service.insert_activity = AsyncMock(return_value=True)
        self.service.postgres_service.get_activities = AsyncMock(return_value=[])

        self.service.client.get_activities.return_value = []

        await self.service.list_activities(session_id)

        # Should fetch with limit when no sync date
        self.service.client.get_activities.assert_called_once_with(limit=50)

    async def test_list_activities_no_session_raises_error(self):
        with self.assertRaises(ValueError) as context:
            await self.service.list_activities("invalid-session")

        self.assertIn("No token found", str(context.exception))

    async def test_list_activities_sets_token_on_client(self):
        session_id = "test-session-123"
        self.service.tokens[session_id] = "mock_token"
        self.service.postgres_service = MagicMock()
        self.service.postgres_service.get_last_sync_date.return_value = None
        self.service.postgres_service.is_activity_synced.return_value = False
        self.service.postgres_service.get_activities = AsyncMock(return_value=[])
        self.service.client.get_activities.return_value = []

        await self.service.list_activities(session_id)

        self.assertEqual(self.service.client.access_token, "mock_token")

    async def test_list_activities_with_custom_limit(self):
        session_id = "test-session-123"
        self.service.tokens[session_id] = "mock_token"
        self.service.postgres_service = MagicMock()
        self.service.postgres_service.get_last_sync_date.return_value = None
        self.service.postgres_service.is_activity_synced.return_value = False
        self.service.postgres_service.get_activities = AsyncMock(return_value=[])
        self.service.client.get_activities.return_value = []

        await self.service.list_activities(session_id, limit=5)

        # Custom limit applies to DB fetch
        self.service.postgres_service.get_activities.assert_called_once_with(limit=5)

    async def test_list_activities_db_failure_raises_error(self):
        session_id = "test-session-123"
        self.service.tokens[session_id] = "mock_token"
        self.service.postgres_service = MagicMock()
        self.service.postgres_service.get_last_sync_date.return_value = None
        self.service.postgres_service.is_activity_synced.return_value = False
        self.service.postgres_service.insert_activity = AsyncMock(
            side_effect=Exception("Database connection failed")
        )

        mock_activity = MagicMock()
        mock_activity.id = 12345
        mock_activity.name = "Morning Run"
        self.service.client.get_activities.return_value = [mock_activity]

        with self.assertRaises(Exception) as context:
            await self.service.list_activities(session_id)

        self.assertIn("Database connection failed", str(context.exception))


if __name__ == "__main__":
    unittest.main()