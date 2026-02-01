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
    db_backend: str = "postgres"

    # Postgres settings
    db_host: str = "127.0.0.1"
    db_port: int = 5432
    db_user: str = "rc-admin"
    db_password: str = "password"
    db_name: str = "postgres"

    # DynamoDB settings
    dynamodb_endpoint_url: str = "http://localhost:9000"
    dynamodb_region: str = "us-east-1"
    dynamodb_table_name: str = "activities"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
