import logging
from datetime import datetime, timedelta, timezone

from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from stravalib.model import SummaryActivity

from src.database.models import Activity


class PostgresService:
    def __init__(self, session_maker: async_sessionmaker[AsyncSession]) -> None:
        self._session_maker = session_maker
        self._last_sync_date: datetime | None = None
        self._initialized: bool = False
        self._synced_ids: set[int] = set()

    async def initialize(self) -> None:
        """Initialize sync state from database. Should be called at startup."""
        if self._initialized:
            return
        logging.info("Initializing PostgresService from database")
        async with self._session_maker() as session:
            # Get the most recent activity date from DB
            result = await session.execute(
                select(func.max(Activity.create_date))
            )
            last_date = result.scalar_one_or_none()
            if last_date:
                self._last_sync_date = last_date
                logging.info(f"Last sync date from DB: {self._last_sync_date}")
            else:
                self._last_sync_date = datetime.now(timezone.utc) - timedelta(days=1)
                logging.info(
                    f"No activities in DB, assuming synced until: {self._last_sync_date}"
                )

            # Load existing activity IDs to avoid duplicates
            result = await session.execute(select(Activity.strava_id))
            self._synced_ids = {row[0] for row in result.all()}
            logging.info(f"Loaded {len(self._synced_ids)} existing activity IDs")

            self._initialized = True

    def get_last_sync_date(self) -> datetime | None:
        """Get the date up to which activities have been synchronized."""
        return self._last_sync_date

    def is_activity_synced(self, strava_id: int) -> bool:
        """Check if an activity has already been synced."""
        return strava_id in self._synced_ids

    async def get_activities(self, limit: int = 100) -> list[SummaryActivity]:
        """Get activities from the database as Pydantic models."""
        logging.info(f"Fetching up to {limit} activities from database")
        async with self._session_maker() as session:
            result = await session.execute(
                select(Activity)
                .order_by(Activity.create_date.desc())
                .limit(limit)
            )
            rows = result.scalars().all()
            logging.info(f"Found {len(rows)} activities in database")

            activities: list[SummaryActivity] = []
            for row in rows:
                try:
                    logging.debug(f"Parsing activity {type(row.strava_response)} {row.strava_response}")
                    activity = SummaryActivity.model_validate(row.strava_response)
                    activities.append(activity)
                    logging.debug(f"Parsed activity {row.strava_id}: {activity.name}")
                except ValidationError as e:
                    logging.error(f"Failed to parse activity {row.strava_id}: {e}")

            logging.info(f"Returning {len(activities)} parsed activities")
            return activities

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
        async with self._session_maker() as session:
            db_activity = Activity(
                strava_id=activity.id,
                create_date=activity.start_date,
                strava_response=activity.model_dump_json(),
            )
            session.add(db_activity)
            await session.commit()
            self._synced_ids.add(activity.id)

            # Update last sync date if this activity is newer
            if activity.start_date and (
                self._last_sync_date is None
                or activity.start_date > self._last_sync_date
            ):
                self._last_sync_date = activity.start_date

            logging.info(f"Activity {activity.id} inserted successfully")
            return True
