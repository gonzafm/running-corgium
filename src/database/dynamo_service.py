from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

from pydantic import ValidationError
from stravalib.model import SummaryActivity

from src.database.activity_repository import ActivityRepository

if TYPE_CHECKING:
    from mypy_boto3_dynamodb.service_resource import Table


class DynamoService(ActivityRepository):
    def __init__(self, table: Table) -> None:
        self._table: Table = table
        self._last_sync_date: datetime | None = None
        self._initialized: bool = False
        self._synced_ids: set[int] = set()

    async def initialize(self) -> None:
        """Initialize sync state from DynamoDB. Should be called at startup."""
        if self._initialized:
            return
        logging.info("Initializing DynamoService from DynamoDB")
        raw = await asyncio.to_thread(
            lambda: self._table.scan(ProjectionExpression="strava_id,create_date")
        )
        items: list[dict[str, Any]] = list(raw.get("Items", []))

        max_date: datetime | None = None
        for item in items:
            self._synced_ids.add(int(item["strava_id"]))
            date_str = item.get("create_date")
            if isinstance(date_str, str):
                dt = datetime.fromisoformat(date_str)
                if max_date is None or dt > max_date:
                    max_date = dt

        if max_date:
            self._last_sync_date = max_date
            logging.info(f"Last sync date from DynamoDB: {self._last_sync_date}")
        else:
            self._last_sync_date = None
            logging.info("No activities in DynamoDB, will fetch recent activities")

        logging.info(f"Loaded {len(self._synced_ids)} existing activity IDs")
        self._initialized = True

    def get_last_sync_date(self) -> datetime | None:
        """Get the date up to which activities have been synchronized."""
        return self._last_sync_date

    def is_activity_synced(self, strava_id: int) -> bool:
        """Check if an activity has already been synced."""
        return strava_id in self._synced_ids

    async def get_activities(self, limit: int = 100) -> list[SummaryActivity]:
        """Get activities from DynamoDB as Pydantic models."""
        logging.info(f"Fetching up to {limit} activities from DynamoDB")
        raw = await asyncio.to_thread(lambda: self._table.scan())
        items: list[dict[str, Any]] = list(raw.get("Items", []))

        # DynamoDB doesn't support ORDER BY — sort in Python
        items.sort(key=lambda x: str(x.get("create_date", "")), reverse=True)
        items = items[:limit]
        logging.info(f"Found {len(items)} activities in DynamoDB")

        activities: list[SummaryActivity] = []
        for item in items:
            try:
                activity = SummaryActivity.model_validate_json(
                    str(item["strava_response"])
                )
                activities.append(activity)
                logging.debug(f"Parsed activity {item['strava_id']}: {activity.name}")
            except (ValidationError, KeyError) as e:
                logging.error(f"Failed to parse activity {item.get('strava_id')}: {e}")

        logging.info(f"Returning {len(activities)} parsed activities")
        return activities

    async def insert_activity(self, activity: SummaryActivity) -> bool:
        """Insert a new activity into DynamoDB."""
        await self.initialize()

        if activity.id is None:
            logging.warning("Activity has no ID, skipping insert")
            return False

        if activity.id in self._synced_ids:
            logging.info(f"Activity {activity.id} already synced, skipping insert")
            return False

        logging.info(f"Inserting activity {activity.id} into DynamoDB")
        item: dict[str, Any] = {
            "strava_id": str(activity.id),
            "strava_response": activity.model_dump_json(),
        }
        if activity.start_date:
            item["create_date"] = activity.start_date.isoformat()

        await asyncio.to_thread(lambda: self._table.put_item(Item=item))
        self._synced_ids.add(activity.id)

        if activity.start_date and (
            self._last_sync_date is None or activity.start_date > self._last_sync_date
        ):
            self._last_sync_date = activity.start_date

        logging.info(f"Activity {activity.id} inserted successfully")
        return True


async def ensure_dynamo_table(
    endpoint_url: str | None, region: str, table_name: str
) -> None:
    """Create the activities table in DynamoDB if it doesn't exist."""
    import boto3

    dynamodb = boto3.resource("dynamodb", endpoint_url=endpoint_url, region_name=region)
    existing: list[str] = await asyncio.to_thread(
        lambda: dynamodb.meta.client.list_tables()["TableNames"]
    )
    if table_name in existing:
        logging.info(f"DynamoDB table '{table_name}' already exists")
        return

    logging.info(f"Creating DynamoDB table '{table_name}'")
    table = await asyncio.to_thread(
        lambda: dynamodb.create_table(
            TableName=table_name,
            KeySchema=[{"AttributeName": "strava_id", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "strava_id", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
    )
    await asyncio.to_thread(table.wait_until_exists)
    logging.info(f"DynamoDB table '{table_name}' created")
