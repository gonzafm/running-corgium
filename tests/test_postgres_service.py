import unittest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone, timedelta

from src.database.postgres_service import PostgresService


class TestPostgresService(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.service = PostgresService()

    def _create_mock_pool(
        self,
        existing_ids: list[int] | None = None,
        last_date: datetime | None = None,
    ) -> tuple[MagicMock, AsyncMock]:
        """Helper to create a mock pool with optional existing data."""
        if existing_ids is None:
            existing_ids = []

        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = {"last_date": last_date}
        mock_conn.fetch.return_value = [{"strava_id": id} for id in existing_ids]

        mock_acquire_cm = AsyncMock()
        mock_acquire_cm.__aenter__.return_value = mock_conn
        mock_acquire_cm.__aexit__.return_value = None

        mock_pool = MagicMock()
        mock_pool.acquire.return_value = mock_acquire_cm
        mock_pool.close = AsyncMock()

        return mock_pool, mock_conn

    @patch("src.database.postgres_service.asyncpg.create_pool", new_callable=AsyncMock)
    async def test_initialize_with_existing_activities(self, mock_create_pool: AsyncMock) -> None:
        last_date = datetime(2024, 1, 15, 8, 0, 0, tzinfo=timezone.utc)
        existing_ids = [111, 222, 333]
        mock_pool, _ = self._create_mock_pool(
            existing_ids=existing_ids, last_date=last_date
        )
        mock_create_pool.return_value = mock_pool

        await self.service.initialize()

        self.assertTrue(self.service._initialized)
        self.assertEqual(self.service._last_sync_date, last_date)
        self.assertEqual(self.service._synced_ids, {111, 222, 333})

    @patch("src.database.postgres_service.asyncpg.create_pool", new_callable=AsyncMock)
    async def test_initialize_with_empty_database(self, mock_create_pool: AsyncMock) -> None:
        mock_pool, _ = self._create_mock_pool(existing_ids=[], last_date=None)
        mock_create_pool.return_value = mock_pool

        await self.service.initialize()

        self.assertTrue(self.service._initialized)
        # Should default to yesterday
        self.assertIsNotNone(self.service._last_sync_date)
        assert self.service._last_sync_date is not None  # for mypy
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        self.assertAlmostEqual(
            self.service._last_sync_date.timestamp(),
            yesterday.timestamp(),
            delta=60,  # Allow 60 seconds difference
        )
        self.assertEqual(self.service._synced_ids, set())

    @patch("src.database.postgres_service.asyncpg.create_pool", new_callable=AsyncMock)
    async def test_initialize_only_runs_once(self, mock_create_pool: AsyncMock) -> None:
        mock_pool, _ = self._create_mock_pool()
        mock_create_pool.return_value = mock_pool

        await self.service.initialize()
        await self.service.initialize()

        # Pool should only be created once
        self.assertEqual(mock_create_pool.await_count, 1)

    @patch("src.database.postgres_service.asyncpg.create_pool", new_callable=AsyncMock)
    async def test_insert_activity_success(self, mock_create_pool: AsyncMock) -> None:
        mock_pool, mock_conn = self._create_mock_pool()
        mock_create_pool.return_value = mock_pool

        mock_activity = MagicMock()
        mock_activity.id = 12345
        mock_activity.start_date = datetime(2024, 1, 15, 8, 0, 0, tzinfo=timezone.utc)
        mock_activity.model_dump_json.return_value = (
            '{"id": 12345, "name": "Morning Run"}'
        )

        result = await self.service.insert_activity(mock_activity)

        self.assertTrue(result)
        mock_conn.execute.assert_called_once_with(
            "INSERT INTO running_corgium.activities(create_date,strava_response,strava_id) VALUES ($1, $2,$3)",
            mock_activity.start_date,
            '{"id": 12345, "name": "Morning Run"}',
            12345,
        )
        self.assertIn(12345, self.service._synced_ids)

    @patch("src.database.postgres_service.asyncpg.create_pool", new_callable=AsyncMock)
    async def test_insert_activity_skipped_when_already_synced(self, mock_create_pool: AsyncMock) -> None:
        existing_id = 12345
        mock_pool, mock_conn = self._create_mock_pool(existing_ids=[existing_id])
        mock_create_pool.return_value = mock_pool

        mock_activity = MagicMock()
        mock_activity.id = existing_id

        result = await self.service.insert_activity(mock_activity)

        self.assertFalse(result)
        mock_conn.execute.assert_not_called()

    @patch("src.database.postgres_service.asyncpg.create_pool", new_callable=AsyncMock)
    async def test_insert_activity_updates_last_sync_date(self, mock_create_pool: AsyncMock) -> None:
        old_date = datetime(2024, 1, 10, 0, 0, 0, tzinfo=timezone.utc)
        new_date = datetime(2024, 1, 15, 8, 0, 0, tzinfo=timezone.utc)
        mock_pool, _ = self._create_mock_pool(last_date=old_date)
        mock_create_pool.return_value = mock_pool

        mock_activity = MagicMock()
        mock_activity.id = 12345
        mock_activity.start_date = new_date
        mock_activity.model_dump_json.return_value = '{"id": 12345}'

        await self.service.insert_activity(mock_activity)

        self.assertEqual(self.service._last_sync_date, new_date)

    @patch("src.database.postgres_service.asyncpg.create_pool", new_callable=AsyncMock)
    async def test_insert_activity_connection_failure(self, mock_create_pool: AsyncMock) -> None:
        mock_create_pool.side_effect = Exception("Connection refused")

        mock_activity = MagicMock()
        mock_activity.id = 12345

        with self.assertRaises(Exception) as context:
            await self.service.insert_activity(mock_activity)

        self.assertIn("Connection refused", str(context.exception))

    @patch("src.database.postgres_service.asyncpg.create_pool", new_callable=AsyncMock)
    async def test_insert_activity_with_none_id(self, mock_create_pool: AsyncMock) -> None:
        mock_pool, mock_conn = self._create_mock_pool()
        mock_create_pool.return_value = mock_pool

        mock_activity = MagicMock()
        mock_activity.id = None

        result = await self.service.insert_activity(mock_activity)

        self.assertFalse(result)
        mock_conn.execute.assert_not_called()

    @patch("src.database.postgres_service.asyncpg.create_pool", new_callable=AsyncMock)
    async def test_get_activities(self, mock_create_pool: AsyncMock) -> None:
        from stravalib.strava_model import SummaryActivity

        mock_pool, mock_conn = self._create_mock_pool()
        create_date = datetime(2024, 1, 15, 8, 0, 0, tzinfo=timezone.utc)
        # Use valid JSON that SummaryActivity can parse
        mock_conn.fetch.return_value = [
            {
                "strava_id": 111,
                "strava_response": '{"id": 111, "name": "Morning Run", "distance": 5000, "type": "Run"}',
                "create_date": create_date,
            },
            {
                "strava_id": 222,
                "strava_response": '{"id": 222, "name": "Evening Walk", "distance": 2000, "type": "Walk"}',
                "create_date": None,
            },
        ]
        mock_create_pool.return_value = mock_pool

        result = await self.service.get_activities(limit=10)

        self.assertEqual(len(result), 2)
        # Verify returned objects are SummaryActivity instances
        self.assertIsInstance(result[0], SummaryActivity)
        self.assertIsInstance(result[1], SummaryActivity)
        # Verify fields are parsed correctly
        self.assertEqual(result[0].name, "Morning Run")
        self.assertEqual(result[0].id, 111)
        self.assertEqual(result[1].name, "Evening Walk")
        self.assertEqual(result[1].id, 222)
        mock_conn.fetch.assert_called_once()

    def test_get_last_sync_date(self):
        test_date = datetime(2024, 1, 15, tzinfo=timezone.utc)
        self.service._last_sync_date = test_date

        result = self.service.get_last_sync_date()

        self.assertEqual(result, test_date)

    def test_is_activity_synced(self):
        self.service._synced_ids = {111, 222, 333}

        self.assertTrue(self.service.is_activity_synced(111))
        self.assertTrue(self.service.is_activity_synced(222))
        self.assertFalse(self.service.is_activity_synced(999))


class TestPostgresServiceConnectionPooling(unittest.IsolatedAsyncioTestCase):
    """Tests for connection pooling behavior."""

    def setUp(self) -> None:
        self.service = PostgresService()

    def _create_mock_pool(
        self,
        existing_ids: list[int] | None = None,
        last_date: datetime | None = None,
    ) -> MagicMock:
        """Helper to create a mock connection pool."""
        if existing_ids is None:
            existing_ids = []

        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = {"last_date": last_date}
        mock_conn.fetch.return_value = [{"strava_id": id} for id in existing_ids]

        # Create a proper async context manager for acquire()
        mock_acquire_cm = AsyncMock()
        mock_acquire_cm.__aenter__.return_value = mock_conn
        mock_acquire_cm.__aexit__.return_value = None

        mock_pool = MagicMock()
        mock_pool.acquire.return_value = mock_acquire_cm
        mock_pool.close = AsyncMock()

        return mock_pool

    @patch("src.database.postgres_service.asyncpg.create_pool", new_callable=AsyncMock)
    async def test_pool_created_on_first_initialize(self, mock_create_pool: AsyncMock) -> None:
        """Verify that a connection pool is created, not individual connections."""
        mock_pool = self._create_mock_pool()
        mock_create_pool.return_value = mock_pool

        await self.service.initialize()

        mock_create_pool.assert_awaited_once()
        # Verify pool configuration includes min/max size
        call_kwargs = mock_create_pool.call_args.kwargs
        self.assertIn("min_size", call_kwargs)
        self.assertIn("max_size", call_kwargs)

    @patch("src.database.postgres_service.asyncpg.create_pool", new_callable=AsyncMock)
    async def test_pool_reused_across_operations(self, mock_create_pool: AsyncMock) -> None:
        """Verify that the same pool is reused for multiple operations."""
        mock_pool = self._create_mock_pool()
        mock_create_pool.return_value = mock_pool

        await self.service.initialize()
        await self.service.get_activities(limit=10)
        await self.service.get_activities(limit=20)

        # Pool should only be created once
        self.assertEqual(mock_create_pool.await_count, 1)
        # But acquire should be called for each operation (including initialize)
        self.assertGreaterEqual(mock_pool.acquire.call_count, 2)

    @patch("src.database.postgres_service.asyncpg.create_pool", new_callable=AsyncMock)
    async def test_connection_acquired_from_pool(self, mock_create_pool: AsyncMock) -> None:
        """Verify connections are acquired from pool, not created individually."""
        mock_pool = self._create_mock_pool()
        mock_create_pool.return_value = mock_pool

        await self.service.initialize()

        # Verify acquire was used as async context manager
        mock_pool.acquire.assert_called()

    @patch("src.database.postgres_service.asyncpg.create_pool", new_callable=AsyncMock)
    async def test_connection_released_after_operation(self, mock_create_pool: AsyncMock) -> None:
        """Verify connections are released back to pool (not closed)."""
        mock_pool = self._create_mock_pool()
        mock_create_pool.return_value = mock_pool

        # Get the mock connection from the pool
        mock_conn = mock_pool.acquire.return_value.__aenter__.return_value

        await self.service.initialize()

        # Connection should NOT be explicitly closed (pool manages this)
        mock_conn.close.assert_not_called()

    @patch("src.database.postgres_service.asyncpg.create_pool", new_callable=AsyncMock)
    async def test_pool_close_on_shutdown(self, mock_create_pool: AsyncMock) -> None:
        """Verify pool is properly closed during shutdown."""
        mock_pool = self._create_mock_pool()
        mock_create_pool.return_value = mock_pool

        await self.service.initialize()
        await self.service.close()

        mock_pool.close.assert_awaited_once()

    @patch("src.database.postgres_service.asyncpg.create_pool", new_callable=AsyncMock)
    async def test_insert_uses_pool_connection(self, mock_create_pool: AsyncMock) -> None:
        """Verify insert_activity uses pooled connection."""
        mock_pool = self._create_mock_pool()
        mock_create_pool.return_value = mock_pool

        mock_activity = MagicMock()
        mock_activity.id = 12345
        mock_activity.start_date = datetime(2024, 1, 15, 8, 0, 0, tzinfo=timezone.utc)
        mock_activity.model_dump_json.return_value = '{"id": 12345}'

        await self.service.initialize()
        initial_acquire_count = mock_pool.acquire.call_count

        await self.service.insert_activity(mock_activity)

        # Should have acquired a connection for the insert
        self.assertGreater(mock_pool.acquire.call_count, initial_acquire_count)

    @patch("src.database.postgres_service.asyncpg.create_pool", new_callable=AsyncMock)
    async def test_get_activities_uses_pool_connection(self, mock_create_pool: AsyncMock) -> None:
        """Verify get_activities uses pooled connection."""
        mock_pool = self._create_mock_pool()
        mock_create_pool.return_value = mock_pool

        await self.service.initialize()
        initial_acquire_count = mock_pool.acquire.call_count

        await self.service.get_activities(limit=10)

        self.assertGreater(mock_pool.acquire.call_count, initial_acquire_count)

    @patch("src.database.postgres_service.asyncpg.create_pool", new_callable=AsyncMock)
    async def test_pool_not_created_if_already_exists(self, mock_create_pool: AsyncMock) -> None:
        """Verify pool is only created once even with multiple initialize calls."""
        mock_pool = self._create_mock_pool()
        mock_create_pool.return_value = mock_pool

        await self.service.initialize()
        await self.service.initialize()
        await self.service.initialize()

        self.assertEqual(mock_create_pool.await_count, 1)

    @patch("src.database.postgres_service.asyncpg.create_pool", new_callable=AsyncMock)
    async def test_pool_configuration_uses_settings(self, mock_create_pool: AsyncMock) -> None:
        """Verify pool is configured with database settings."""
        mock_pool = self._create_mock_pool()
        mock_create_pool.return_value = mock_pool

        await self.service.initialize()

        call_kwargs = mock_create_pool.call_args.kwargs
        # Should use settings for connection parameters
        self.assertIn("host", call_kwargs)
        self.assertIn("database", call_kwargs)
        self.assertIn("user", call_kwargs)
        self.assertIn("password", call_kwargs)


if __name__ == "__main__":
    unittest.main()