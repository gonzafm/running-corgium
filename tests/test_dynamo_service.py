"""Behavioral contract tests for DynamoService.

These tests verify that DynamoService satisfies the ActivityRepository
contract.  They mock the boto3 DynamoDB Table resource and test the same
observable behaviours as PostgresService.

Expected DynamoDB table schema:
    Partition key: strava_id (N)
    Attributes:    create_date (S, ISO-8601), strava_response (S, JSON)

Tests are skipped automatically until ``src.database.dynamo_service.DynamoService``
exists.
"""

import unittest
from decimal import Decimal
from unittest.mock import MagicMock
from datetime import datetime, timezone, timedelta

from src.database.dynamo_service import DynamoService


class TestDynamoService(unittest.IsolatedAsyncioTestCase):
    """Contract tests — same behavioural expectations as PostgresService."""

    def setUp(self) -> None:
        self.mock_table = MagicMock()
        self.service = DynamoService(self.mock_table)

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    def _setup_initialize(
        self,
        last_date: datetime | None = None,
        existing_ids: list[int] | None = None,
    ) -> None:
        """Configure mock table.scan() for initialize().

        Each item carries ``strava_id`` (Decimal, as boto3 returns) and
        optionally ``create_date`` (ISO-8601 string).
        """
        if existing_ids is None:
            existing_ids = []

        items: list[dict[str, Decimal | str]] = []
        for sid in existing_ids:
            item: dict[str, Decimal | str] = {"strava_id": Decimal(str(sid))}
            if last_date is not None:
                item["create_date"] = last_date.isoformat()
            items.append(item)

        self.mock_table.scan.return_value = {
            "Items": items,
            "Count": len(items),
        }

    # ------------------------------------------------------------------
    # initialize()
    # ------------------------------------------------------------------

    async def test_initialize_with_existing_activities(self) -> None:
        last_date = datetime(2024, 1, 15, 8, 0, 0, tzinfo=timezone.utc)
        existing_ids = [111, 222, 333]
        self._setup_initialize(last_date=last_date, existing_ids=existing_ids)

        await self.service.initialize()

        self.assertEqual(self.service.get_last_sync_date(), last_date)
        for sid in existing_ids:
            self.assertTrue(self.service.is_activity_synced(sid))

    async def test_initialize_with_empty_database(self) -> None:
        self._setup_initialize(last_date=None, existing_ids=[])

        await self.service.initialize()

        last_sync = self.service.get_last_sync_date()
        self.assertIsNone(last_sync)

    async def test_initialize_only_runs_once(self) -> None:
        self._setup_initialize()

        await self.service.initialize()
        await self.service.initialize()

        # The table should only be scanned during the first call
        self.assertEqual(self.mock_table.scan.call_count, 1)

    # ------------------------------------------------------------------
    # insert_activity()
    # ------------------------------------------------------------------

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
        self.mock_table.put_item.assert_called_once()
        self.assertTrue(self.service.is_activity_synced(12345))

    async def test_insert_activity_skipped_when_already_synced(self) -> None:
        existing_id = 12345
        self._setup_initialize(existing_ids=[existing_id])

        mock_activity = MagicMock()
        mock_activity.id = existing_id

        result = await self.service.insert_activity(mock_activity)

        self.assertFalse(result)
        self.mock_table.put_item.assert_not_called()

    async def test_insert_activity_updates_last_sync_date(self) -> None:
        old_date = datetime(2024, 1, 10, 0, 0, 0, tzinfo=timezone.utc)
        new_date = datetime(2024, 1, 15, 8, 0, 0, tzinfo=timezone.utc)
        # Need an existing item so the scan returns old_date as the max
        self._setup_initialize(last_date=old_date, existing_ids=[99999])

        mock_activity = MagicMock()
        mock_activity.id = 12345
        mock_activity.start_date = new_date
        mock_activity.model_dump_json.return_value = '{"id": 12345}'

        await self.service.insert_activity(mock_activity)

        self.assertEqual(self.service.get_last_sync_date(), new_date)

    async def test_insert_activity_with_none_id(self) -> None:
        self._setup_initialize()

        mock_activity = MagicMock()
        mock_activity.id = None

        result = await self.service.insert_activity(mock_activity)

        self.assertFalse(result)
        self.mock_table.put_item.assert_not_called()

    # ------------------------------------------------------------------
    # get_activities()
    # ------------------------------------------------------------------

    async def test_get_activities(self) -> None:
        from stravalib.strava_model import SummaryActivity

        self.mock_table.scan.return_value = {
            "Items": [
                {
                    "strava_id": Decimal("111"),
                    "strava_response": '{"id": 111, "name": "Morning Run", "distance": 5000, "type": "Run"}',
                    "create_date": "2024-01-15T08:00:00+00:00",
                },
                {
                    "strava_id": Decimal("222"),
                    "strava_response": '{"id": 222, "name": "Evening Walk", "distance": 2000, "type": "Walk"}',
                    "create_date": "2024-01-14T18:00:00+00:00",
                },
            ],
            "Count": 2,
        }

        result = await self.service.get_activities(limit=10)

        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], SummaryActivity)
        self.assertIsInstance(result[1], SummaryActivity)
        # Should be ordered by date descending
        self.assertEqual(result[0].name, "Morning Run")
        self.assertEqual(result[1].name, "Evening Walk")

    async def test_get_activities_respects_limit(self) -> None:
        items = [
            {
                "strava_id": Decimal(str(i)),
                "strava_response": f'{{"id": {i}, "name": "Run {i}"}}',
                "create_date": f"2024-01-{i:02d}T08:00:00+00:00",
            }
            for i in range(1, 11)
        ]
        self.mock_table.scan.return_value = {"Items": items, "Count": 10}

        result = await self.service.get_activities(limit=3)

        self.assertLessEqual(len(result), 3)

    # ------------------------------------------------------------------
    # get_last_sync_date() / is_activity_synced()
    # ------------------------------------------------------------------

    def test_get_last_sync_date_before_init(self) -> None:
        self.assertIsNone(self.service.get_last_sync_date())

    def test_is_activity_synced_before_init(self) -> None:
        self.assertFalse(self.service.is_activity_synced(999))


class TestDynamoServiceTableUsage(unittest.IsolatedAsyncioTestCase):
    """Tests for DynamoDB table interaction patterns."""

    def setUp(self) -> None:
        self.mock_table = MagicMock()
        self.service = DynamoService(self.mock_table)

    def _setup_initialize(
        self,
        existing_ids: list[int] | None = None,
        last_date: datetime | None = None,
    ) -> None:
        if existing_ids is None:
            existing_ids = []
        items: list[dict[str, Decimal | str]] = []
        for sid in existing_ids:
            item: dict[str, Decimal | str] = {"strava_id": Decimal(str(sid))}
            if last_date is not None:
                item["create_date"] = last_date.isoformat()
            items.append(item)
        self.mock_table.scan.return_value = {
            "Items": items,
            "Count": len(items),
        }

    async def test_table_scanned_on_initialize(self) -> None:
        """Verify that initialize reads from the table."""
        self._setup_initialize()

        await self.service.initialize()

        self.mock_table.scan.assert_called()

    async def test_put_item_called_on_insert(self) -> None:
        """Verify insert uses put_item."""
        self._setup_initialize()

        mock_activity = MagicMock()
        mock_activity.id = 12345
        mock_activity.start_date = datetime(2024, 1, 15, 8, 0, 0, tzinfo=timezone.utc)
        mock_activity.model_dump_json.return_value = '{"id": 12345}'

        await self.service.insert_activity(mock_activity)

        self.mock_table.put_item.assert_called_once()

    async def test_initialize_idempotent(self) -> None:
        """Verify repeated initialize does not re-scan."""
        self._setup_initialize()

        await self.service.initialize()
        await self.service.initialize()
        await self.service.initialize()

        self.assertEqual(self.mock_table.scan.call_count, 1)


if __name__ == "__main__":
    unittest.main()
