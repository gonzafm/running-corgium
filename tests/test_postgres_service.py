import unittest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime, timezone, timedelta

from src.database.postgres_service import PostgresService


class TestPostgresService(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.mock_session = AsyncMock()
        self.mock_session.add = MagicMock()
        self.mock_session_maker = MagicMock()
        self.mock_session_maker.return_value.__aenter__.return_value = self.mock_session
        self.mock_session_maker.return_value.__aexit__.return_value = None
        self.service = PostgresService(self.mock_session_maker)

    def _setup_initialize(
        self,
        last_date: datetime | None = None,
        existing_ids: list[int] | None = None,
    ) -> None:
        """Configure mock session for initialize() calls."""
        if existing_ids is None:
            existing_ids = []

        # First execute call: select(func.max(Activity.create_date))
        max_result = MagicMock()
        max_result.scalar_one_or_none.return_value = last_date

        # Second execute call: select(Activity.strava_id)
        ids_result = MagicMock()
        ids_result.all.return_value = [(sid,) for sid in existing_ids]

        self.mock_session.execute = AsyncMock(side_effect=[max_result, ids_result])

    async def test_initialize_with_existing_activities(self) -> None:
        last_date = datetime(2024, 1, 15, 8, 0, 0, tzinfo=timezone.utc)
        existing_ids = [111, 222, 333]
        self._setup_initialize(last_date=last_date, existing_ids=existing_ids)

        await self.service.initialize()

        self.assertTrue(self.service._initialized)
        self.assertEqual(self.service._last_sync_date, last_date)
        self.assertEqual(self.service._synced_ids, {111, 222, 333})

    async def test_initialize_with_empty_database(self) -> None:
        self._setup_initialize(last_date=None, existing_ids=[])

        await self.service.initialize()

        self.assertTrue(self.service._initialized)
        self.assertIsNotNone(self.service._last_sync_date)
        assert self.service._last_sync_date is not None  # for mypy
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        self.assertAlmostEqual(
            self.service._last_sync_date.timestamp(),
            yesterday.timestamp(),
            delta=60,
        )
        self.assertEqual(self.service._synced_ids, set())

    async def test_initialize_only_runs_once(self) -> None:
        self._setup_initialize()

        await self.service.initialize()
        await self.service.initialize()

        # Session maker should only be called once
        self.mock_session_maker.assert_called_once()

    async def test_insert_activity_success(self) -> None:
        self._setup_initialize()

        mock_activity = MagicMock()
        mock_activity.id = 12345
        mock_activity.start_date = datetime(2024, 1, 15, 8, 0, 0, tzinfo=timezone.utc)
        mock_activity.model_dump_json.return_value = (
            '{"id": 12345, "name": "Morning Run"}'
        )

        result = await self.service.insert_activity(mock_activity)

        self.assertTrue(result)
        self.mock_session.add.assert_called_once()
        self.mock_session.commit.assert_awaited()
        self.assertIn(12345, self.service._synced_ids)

    async def test_insert_activity_skipped_when_already_synced(self) -> None:
        existing_id = 12345
        self._setup_initialize(existing_ids=[existing_id])

        mock_activity = MagicMock()
        mock_activity.id = existing_id

        result = await self.service.insert_activity(mock_activity)

        self.assertFalse(result)

    async def test_insert_activity_updates_last_sync_date(self) -> None:
        old_date = datetime(2024, 1, 10, 0, 0, 0, tzinfo=timezone.utc)
        new_date = datetime(2024, 1, 15, 8, 0, 0, tzinfo=timezone.utc)
        self._setup_initialize(last_date=old_date)

        mock_activity = MagicMock()
        mock_activity.id = 12345
        mock_activity.start_date = new_date
        mock_activity.model_dump_json.return_value = '{"id": 12345}'

        await self.service.insert_activity(mock_activity)

        self.assertEqual(self.service._last_sync_date, new_date)

    async def test_insert_activity_with_none_id(self) -> None:
        self._setup_initialize()

        mock_activity = MagicMock()
        mock_activity.id = None

        result = await self.service.insert_activity(mock_activity)

        self.assertFalse(result)

    async def test_get_activities(self) -> None:
        from stravalib.strava_model import SummaryActivity

        mock_row1 = MagicMock()
        mock_row1.strava_id = 111
        mock_row1.strava_response = {
            "id": 111,
            "name": "Morning Run",
            "distance": 5000,
            "type": "Run",
        }

        mock_row2 = MagicMock()
        mock_row2.strava_id = 222
        mock_row2.strava_response = {
            "id": 222,
            "name": "Evening Walk",
            "distance": 2000,
            "type": "Walk",
        }

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_row1, mock_row2]
        self.mock_session.execute = AsyncMock(return_value=mock_result)

        result = await self.service.get_activities(limit=10)

        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], SummaryActivity)
        self.assertIsInstance(result[1], SummaryActivity)
        self.assertEqual(result[0].name, "Morning Run")
        self.assertEqual(result[0].id, 111)
        self.assertEqual(result[1].name, "Evening Walk")
        self.assertEqual(result[1].id, 222)
        self.mock_session.execute.assert_called_once()

    def test_get_last_sync_date(self) -> None:
        test_date = datetime(2024, 1, 15, tzinfo=timezone.utc)
        self.service._last_sync_date = test_date

        result = self.service.get_last_sync_date()

        self.assertEqual(result, test_date)

    def test_is_activity_synced(self) -> None:
        self.service._synced_ids = {111, 222, 333}

        self.assertTrue(self.service.is_activity_synced(111))
        self.assertTrue(self.service.is_activity_synced(222))
        self.assertFalse(self.service.is_activity_synced(999))


class TestPostgresServiceSessionUsage(unittest.IsolatedAsyncioTestCase):
    """Tests for SQLAlchemy session usage behavior."""

    def setUp(self) -> None:
        self.mock_session = AsyncMock()
        self.mock_session.add = MagicMock()
        self.mock_session_maker = MagicMock()
        self.mock_session_maker.return_value.__aenter__.return_value = self.mock_session
        self.mock_session_maker.return_value.__aexit__.return_value = None
        self.service = PostgresService(self.mock_session_maker)

    def _setup_initialize(
        self,
        existing_ids: list[int] | None = None,
        last_date: datetime | None = None,
    ) -> None:
        if existing_ids is None:
            existing_ids = []

        max_result = MagicMock()
        max_result.scalar_one_or_none.return_value = last_date

        ids_result = MagicMock()
        ids_result.all.return_value = [(sid,) for sid in existing_ids]

        self.mock_session.execute = AsyncMock(side_effect=[max_result, ids_result])

    async def test_session_created_on_initialize(self) -> None:
        """Verify that a session is created during initialization."""
        self._setup_initialize()

        await self.service.initialize()

        self.mock_session_maker.assert_called_once()

    async def test_session_used_for_get_activities(self) -> None:
        """Verify get_activities creates its own session."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        self.mock_session.execute = AsyncMock(return_value=mock_result)

        await self.service.get_activities(limit=10)

        self.mock_session.execute.assert_called_once()

    async def test_session_used_for_insert(self) -> None:
        """Verify insert_activity creates its own session and commits."""
        self._setup_initialize()

        mock_activity = MagicMock()
        mock_activity.id = 12345
        mock_activity.start_date = datetime(2024, 1, 15, 8, 0, 0, tzinfo=timezone.utc)
        mock_activity.model_dump_json.return_value = '{"id": 12345}'

        await self.service.insert_activity(mock_activity)

        self.mock_session.add.assert_called_once()
        self.mock_session.commit.assert_awaited()

    async def test_initialize_only_runs_once(self) -> None:
        """Verify initialize is idempotent."""
        self._setup_initialize()

        await self.service.initialize()
        await self.service.initialize()
        await self.service.initialize()

        # Session maker should only be called once for initialization
        self.mock_session_maker.assert_called_once()

    async def test_insert_activity_commits_transaction(self) -> None:
        """Verify insert commits the transaction."""
        self._setup_initialize()

        mock_activity = MagicMock()
        mock_activity.id = 99999
        mock_activity.start_date = datetime(2024, 1, 15, 8, 0, 0, tzinfo=timezone.utc)
        mock_activity.model_dump_json.return_value = '{"id": 99999}'

        await self.service.insert_activity(mock_activity)

        self.mock_session.commit.assert_awaited()


if __name__ == "__main__":
    unittest.main()
