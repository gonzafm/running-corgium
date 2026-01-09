from stravalib import Client
import logging
from src.config import settings


class StravaService:
    client = None
    tokens = dict()

    def __init__(self):
        self.client = Client()

    def get_basic_info(self):
        logging.info("Getting basic info from Strava")
        url = self.client.authorization_url(
            client_id=settings.strava_client_id,
            redirect_uri=settings.strava_redirect_uri,
        )
        logging.info(f"Please authorize at {url}")
        return url

    def authenticate_and_store(self, code: str):
        logging.info("Authenticating with Strava")
        token_response = self.client.exchange_code_for_token(
            client_id=settings.strava_client_id,
            client_secret=settings.strava_client_secret,
            code=code,
        )
        self.tokens["Gonzalo"] = token_response["access_token"]
        logging.info("Token stored successfully")

    def get_athlete(self):
        return self.client.get_athlete()
