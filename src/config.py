from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    strava_client_id: int
    strava_client_secret: str
    strava_redirect_uri: str = "http://localhost:5173/auth/callback"
    environment: str = "dev"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
