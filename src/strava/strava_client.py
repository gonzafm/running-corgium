import asyncio
import logging

from stravalib import Client
from stravalib.model import SummaryActivity

from src.config import settings
from src.database.activity_repository import ActivityRepository


class StravaService:
    tokens: dict[str, str] = {}

    def __init__(self, activity_repo: ActivityRepository) -> None:
        self.client = Client()
        self.activity_repo = activity_repo

    def get_basic_info(self) -> str:
        logging.info("Getting basic info from Strava")
        url = self.client.authorization_url(
            client_id=settings.strava_client_id,
            redirect_uri=settings.strava_redirect_uri,
        )
        logging.info(f"Please authorize at {url}")
        return url

    async def authenticate_and_store(self, session_id: str, code: str) -> None:
        logging.info("Authenticating with Strava")
        token_response = await asyncio.to_thread(
            self.client.exchange_code_for_token,
            client_id=settings.strava_client_id,
            client_secret=settings.strava_client_secret,
            code=code,
        )
        # Handle union return type: AccessInfo or tuple[AccessInfo, athlete]
        if isinstance(token_response, tuple):
            access_info = token_response[0]
        else:
            access_info = token_response
        self.tokens[session_id] = access_info["access_token"]
        logging.info("Token stored successfully")

    def _get_client_for_session(self, session_id: str) -> Client:
        """Get a client configured with the session's access token."""
        if session_id not in self.tokens:
            raise ValueError(f"No token found for session: {session_id}")
        self.client.access_token = self.tokens[session_id]
        return self.client

    async def list_activities(
        self, session_id: str, limit: int = 100
    ) -> list[SummaryActivity]:
        """Return all activities, syncing new ones from Strava first.

        1. Fetches only NEW activities from Strava API (after last sync date)
        2. Stores new activities in the database
        3. Returns ALL activities from the database as Pydantic models
        """
        logging.info(f"list_activities called for session {session_id}, limit={limit}")
        try:
            client = self._get_client_for_session(session_id)
            logging.info("Client configured successfully")

            # Sync new activities from Strava
            new_count = await self._sync_new_activities(client)
            logging.info(f"Sync complete: {new_count} new activities")

            # Return all activities from database
            db_activities = await self.activity_repo.get_activities(limit=limit)
            logging.info(f"Returning {len(db_activities)} activities from database")
            if db_activities:
                logging.info(
                    f"First activity: {db_activities[0].name} (ID: {db_activities[0].id})"
                )
            return db_activities
        except ValueError:
            raise
        except Exception as e:
            logging.error(f"Error fetching activities: {e}", exc_info=True)
            raise

    async def _sync_new_activities(self, client: Client) -> int:
        """Sync new activities from Strava to the database.

        Only fetches activities after the last sync date to minimize API calls.
        Returns the number of new activities synced.
        """
        last_sync_date = self.activity_repo.get_last_sync_date()
        logging.info(f"Last sync date: {last_sync_date}")

        if last_sync_date:
            logging.info(f"Fetching activities from Strava after {last_sync_date}")
            # Run sync Strava API call in thread to avoid blocking event loop
            results = await asyncio.to_thread(
                lambda: list(client.get_activities(after=last_sync_date))
            )
        else:
            logging.info("No sync date found, fetching recent activities from Strava")
            # Run sync Strava API call in thread to avoid blocking event loop
            results = await asyncio.to_thread(
                lambda: list(client.get_activities(limit=50))
            )

        new_count = 0
        for activity in results:
            logging.info(
                f"Processing activity {activity.id}: {activity.name} "
                f"(start_date: {activity.start_date})"
            )
            if activity.id is not None and not self.activity_repo.is_activity_synced(
                activity.id
            ):
                logging.info(
                    f"Inserting new activity: {activity.name} (ID: {activity.id})"
                )
                inserted = await self.activity_repo.insert_activity(activity)
                if inserted:
                    new_count += 1
                    logging.info(f"Successfully inserted activity {activity.id}")
                else:
                    logging.warning(f"Failed to insert activity {activity.id}")
            else:
                logging.info(f"Activity {activity.id} already synced, skipping")

        logging.info(f"Sync complete: {new_count} new activities synced from Strava")
        return new_count

    async def get_athlete(self, session_id: str):
        """Fetch athlete data for a session."""
        client = self._get_client_for_session(session_id)
        return await asyncio.to_thread(client.get_athlete)
