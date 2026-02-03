import os

from pydantic import SecretStr
from pydantic_settings import BaseSettings
from pydantic_settings.main import PydanticBaseSettingsSource


class Settings(BaseSettings):
    strava_client_id: int
    strava_client_secret: str
    strava_redirect_uri: str = "http://localhost:8000/strava/authorize"
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

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        if "AWS_LAMBDA_FUNCTION_NAME" in os.environ:
            from pydantic_settings.sources.providers.aws import (
                AWSSecretsManagerSettingsSource,
            )

            secret_id = os.environ.get(
                "SECRETS_MANAGER_SECRET_ID", "running-corgium/config"
            )
            aws_source = AWSSecretsManagerSettingsSource(
                settings_cls,
                secret_id=secret_id,
                case_sensitive=False,
            )
            return (init_settings, aws_source, env_settings)
        return (init_settings, env_settings, dotenv_settings, file_secret_settings)


settings = Settings()
