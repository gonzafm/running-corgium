"""Tests for AWS Secrets Manager integration in Settings."""

import json
import os
from unittest.mock import MagicMock, patch

from pydantic_settings.sources.providers.aws import AWSSecretsManagerSettingsSource

from src.config import Settings


class TestLocalModeSourceSelection:
    """In local (non-Lambda) mode, Secrets Manager should not be used."""

    def test_no_aws_source_when_not_lambda(self):
        env = os.environ.copy()
        env.pop("AWS_LAMBDA_FUNCTION_NAME", None)
        with patch.dict(os.environ, env, clear=True):
            sources = Settings.settings_customise_sources(
                Settings,
                init_settings=MagicMock(),
                env_settings=MagicMock(),
                dotenv_settings=MagicMock(),
                file_secret_settings=MagicMock(),
            )
            source_types = {type(s) for s in sources}
            assert AWSSecretsManagerSettingsSource not in source_types


class TestLambdaModeSourceSelection:
    """In Lambda mode, Secrets Manager should be the primary config source."""

    def test_aws_source_included_when_lambda(self):
        mock_secret = {
            "STRAVA_CLIENT_ID": "12345",
            "STRAVA_CLIENT_SECRET": "secret",
            "JWT_SECRET": "jwt-secret",
            "DB_BACKEND": "dynamodb",
        }
        mock_client = MagicMock()
        mock_client.get_secret_value.return_value = {
            "SecretString": json.dumps(mock_secret),
        }

        with (
            patch.dict(
                os.environ,
                {"AWS_LAMBDA_FUNCTION_NAME": "running-corgium"},
                clear=False,
            ),
            patch("boto3.client", return_value=mock_client),
        ):
            sources = Settings.settings_customise_sources(
                Settings,
                init_settings=MagicMock(),
                env_settings=MagicMock(),
                dotenv_settings=MagicMock(),
                file_secret_settings=MagicMock(),
            )
            source_types = [type(s) for s in sources]
            assert AWSSecretsManagerSettingsSource in source_types

    def test_custom_secret_id_from_env(self):
        mock_client = MagicMock()
        mock_client.get_secret_value.return_value = {
            "SecretString": "{}",
        }

        with (
            patch.dict(
                os.environ,
                {
                    "AWS_LAMBDA_FUNCTION_NAME": "my-func",
                    "SECRETS_MANAGER_SECRET_ID": "custom/secret",
                },
                clear=False,
            ),
            patch("boto3.client", return_value=mock_client),
        ):
            sources = Settings.settings_customise_sources(
                Settings,
                init_settings=MagicMock(),
                env_settings=MagicMock(),
                dotenv_settings=MagicMock(),
                file_secret_settings=MagicMock(),
            )
            aws_source = next(
                s for s in sources if isinstance(s, AWSSecretsManagerSettingsSource)
            )
            assert aws_source._secret_id == "custom/secret"

    def test_default_secret_id(self):
        mock_client = MagicMock()
        mock_client.get_secret_value.return_value = {
            "SecretString": "{}",
        }

        env = os.environ.copy()
        env.pop("SECRETS_MANAGER_SECRET_ID", None)
        env["AWS_LAMBDA_FUNCTION_NAME"] = "my-func"

        with (
            patch.dict(os.environ, env, clear=True),
            patch("boto3.client", return_value=mock_client),
        ):
            sources = Settings.settings_customise_sources(
                Settings,
                init_settings=MagicMock(),
                env_settings=MagicMock(),
                dotenv_settings=MagicMock(),
                file_secret_settings=MagicMock(),
            )
            aws_source = next(
                s for s in sources if isinstance(s, AWSSecretsManagerSettingsSource)
            )
            assert aws_source._secret_id == "running-corgium/config"

    def test_settings_loads_from_secret(self):
        mock_secret = {
            "STRAVA_CLIENT_ID": "99999",
            "STRAVA_CLIENT_SECRET": "from-secrets-manager",
            "JWT_SECRET": "sm-jwt-secret",
            "DB_BACKEND": "dynamodb",
            "DYNAMODB_REGION": "eu-west-1",
            "DYNAMODB_TABLE_NAME": "my-activities",
        }
        mock_client = MagicMock()
        mock_client.get_secret_value.return_value = {
            "SecretString": json.dumps(mock_secret),
        }

        with (
            patch.dict(
                os.environ,
                {"AWS_LAMBDA_FUNCTION_NAME": "my-func"},
                clear=True,
            ),
            patch("boto3.client", return_value=mock_client),
        ):
            s = Settings()

            assert s.strava_client_id == 99999
            assert s.strava_client_secret == "from-secrets-manager"
            assert s.jwt_secret.get_secret_value() == "sm-jwt-secret"
            assert s.db_backend == "dynamodb"
            assert s.dynamodb_region == "eu-west-1"
            assert s.dynamodb_table_name == "my-activities"
