import asyncpg
import json
from datetime import datetime, timedelta, timezone
from stravalib.strava_model import SummaryActivity
import logging


class PostgresService:
    def __init__(self) -> None:
        self._last_sync_date: datetime | None = None
        self._initialized: bool = False
        self._synced_ids: set[int] = set()

    async def _get_connection(self) -> asyncpg.Connection:
        return await asyncpg.connect(
            user="rc-admin", password="password", database="postgres", host="127.0.0.1"
        )

    async def initialize(self) -> None:
        """Initialize sync state from database. Should be called at startup."""
        if self._initialized:
            return
        logging.info("Initializing PostgresService from database")
        conn = await self._get_connection()
        try:
            # Get the most recent activity date from DB
            row = await conn.fetchrow(
                "SELECT MAX(create_date) as last_date FROM running_corgium.activities"
            )
            if row and row["last_date"]:
                self._last_sync_date = row["last_date"]
                logging.info(f"Last sync date from DB: {self._last_sync_date}")
            else:
                # No activities in DB, assume everything until yesterday is synced
                self._last_sync_date = datetime.now(timezone.utc) - timedelta(days=1)
                logging.info(
                    f"No activities in DB, assuming synced until: {self._last_sync_date}"
                )

            # Load existing activity IDs to avoid duplicates
            rows = await conn.fetch(
                "SELECT strava_id FROM running_corgium.activities"
            )
            self._synced_ids = {row["strava_id"] for row in rows}
            logging.info(f"Loaded {len(self._synced_ids)} existing activity IDs")

            self._initialized = True
        finally:
            await conn.close()

    def get_last_sync_date(self) -> datetime | None:
        """Get the date up to which activities have been synchronized."""
        return self._last_sync_date

    def is_activity_synced(self, strava_id: int) -> bool:
        """Check if an activity has already been synced."""
        return strava_id in self._synced_ids

    async def get_activities(self, limit: int = 100) -> list[dict]:
        """Get activities from the database, parsing the stored JSON response."""
        logging.info(f"Fetching up to {limit} activities from database")
        conn = await self._get_connection()
        try:
            rows = await conn.fetch(
                """SELECT strava_id, strava_response, create_date
                   FROM running_corgium.activities
                   ORDER BY create_date DESC
                   LIMIT $1""",
                limit,
            )
            logging.info(f"Found {len(rows)} activities in database")

            activities = []
            for row in rows:
                try:
                    # Parse the stored JSON response
                    activity_data = json.loads(row["strava_response"])
                    activity_data["strava_id"] = row["strava_id"]
                    activity_data["create_date"] = (
                        row["create_date"].isoformat() if row["create_date"] else None
                    )
                    activities.append(activity_data)
                    logging.debug(f"Parsed activity {row['strava_id']}: {activity_data.get('name', 'Unknown')}")
                except json.JSONDecodeError as e:
                    logging.error(f"Failed to parse activity {row['strava_id']}: {e}")

            logging.info(f"Returning {len(activities)} parsed activities")
            return activities
        finally:
            await conn.close()

    async def insert_activity(self, activity: SummaryActivity) -> bool:
        """Insert a new activity into the database."""
        await self.initialize()

        if activity.id is None:
            logging.warning("Activity has no ID, skipping insert")
            return False

        if activity.id in self._synced_ids:
            logging.info(f"Activity {activity.id} already synced, skipping insert")
            return False

        logging.info(f"Inserting activity {activity.id} into database")
        conn = await self._get_connection()
        try:
            await conn.execute(
                "INSERT INTO running_corgium.activities(create_date,strava_response,strava_id) VALUES ($1, $2,$3)",
                activity.start_date,
                activity.model_dump_json(),
                activity.id,
            )
            self._synced_ids.add(activity.id)

            # Update last sync date if this activity is newer
            if activity.start_date and (
                self._last_sync_date is None
                or activity.start_date > self._last_sync_date
            ):
                self._last_sync_date = activity.start_date

            logging.info(f"Activity {activity.id} inserted successfully")
            return True
        finally:
            await conn.close()