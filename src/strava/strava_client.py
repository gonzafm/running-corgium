from stravalib import Client
import logging

from stravalib.model import Duration, RelaxedActivityType, SummaryActivity

from src.config import settings


class StravaService:
    tokens: dict[str, str] = {}

    def __init__(self) -> None:
        self.client = Client()

    def get_basic_info(self) -> str:
        logging.info("Getting basic info from Strava")
        url = self.client.authorization_url(
            client_id=settings.strava_client_id,
            redirect_uri=settings.strava_redirect_uri,
        )
        logging.info(f"Please authorize at {url}")
        return url

    def authenticate_and_store(self, session_id: str, code: str) -> None:
        logging.info("Authenticating with Strava")
        token_response = self.client.exchange_code_for_token(
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

    def list_activities(self, session_id: str, limit: int = 10) -> list[dict]:
        """Fetch activities for a session and return as a list of dicts."""
        try:
            client = self._get_client_for_session(session_id)
            results = client.get_activities(limit=limit)
            activities = []
            for activity in results:
                logging.info(f"Activity: {activity.name}")
                activities.append(self.map_activity(activity))
            return activities
        except ValueError:
            raise
        except Exception as e:
            logging.error(f"Error fetching activities: {e}")
            raise

    def map_activity(self,
                     activity: SummaryActivity) -> dict[str, int | None | str | float | Duration | RelaxedActivityType]:
        return {
            "id": activity.id,
            "name": activity.name,
            "distance": float(activity.distance) if activity.distance else 0,
            "moving_time": activity.moving_time if activity.moving_time else 0,
            "elapsed_time": activity.elapsed_time if activity.elapsed_time else 0,
            "total_elevation_gain": float(activity.total_elevation_gain) if activity.total_elevation_gain else 0,
            "type": activity.type,
            "start_date": activity.start_date.isoformat() if activity.start_date else None,
            "start_date_local": activity.start_date_local.isoformat() if activity.start_date_local else None,
            "timezone": str(activity.timezone) if activity.timezone else None,
        }

    def get_athlete(self, session_id: str):
        """Fetch athlete data for a session."""
        client = self._get_client_for_session(session_id)
        return client.get_athlete()
