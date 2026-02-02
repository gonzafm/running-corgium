import os

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    strava_client_id: int
    strava_client_secret: str
    strava_redirect_uri: str = "http://localhost:5173/auth/callback"
    environment: str = "dev"

    # JWT settings
    jwt_secret: SecretStr
    jwt_lifetime_seconds: int = 3600

    # Storage backend: "postgres" or "dynamodb"
    db_backend: str = "standalone"

    # Postgres settings
    db_host: str = "127.0.0.1"
    db_port: int = 5432
    db_user: str = "rc-admin"
    db_password: str = "password"
    db_name: str = "postgres"

    # DynamoDB settings
    dynamodb_endpoint_url: str | None = None
    dynamodb_region: str = "us-east-2"
    dynamodb_table_name: str = "activities"

    # MSK settings (standalone export)
    msk_bootstrap_servers: str = ""
    msk_topic: str = "user-migration"
    msk_region: str = "us-east-2"

    @property
    def is_lambda(self) -> bool:
        return "AWS_LAMBDA_FUNCTION_NAME" in os.environ

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
