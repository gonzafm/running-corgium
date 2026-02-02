import json
import logging
import ssl
from datetime import datetime
from typing import Any

from aiokafka import AIOKafkaProducer
from aiokafka.abc import AbstractTokenProvider
from aws_msk_iam_sasl_signer import MSKAuthTokenProvider

from src.config import settings

logger = logging.getLogger(__name__)


class MSKTokenProvider(AbstractTokenProvider):
    """OAUTHBEARER token provider for Amazon MSK IAM authentication."""

    def __init__(self, region: str) -> None:
        super().__init__()
        self._region = region

    async def token(self) -> str:
        token, _ = MSKAuthTokenProvider.generate_auth_token(self._region)
        return token


def serialize_user(user: Any) -> dict[str, Any]:
    """Convert a SQLAlchemy User row to a JSON-serializable dict.

    Uses the model's __table__.columns to capture all column names,
    converting datetime fields to ISO 8601 strings.
    """
    data: dict[str, Any] = {}
    for column in user.__table__.columns:
        value = getattr(user, column.key)
        if isinstance(value, datetime):
            value = value.isoformat()
        data[column.key] = value
    return data


async def send_users_to_msk(users: list[dict[str, Any]]) -> int:
    """Send each user dict as a Kafka message to the configured MSK topic.

    Creates a producer per call, sends all messages, then closes.
    Returns the number of messages sent.
    """
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    producer = AIOKafkaProducer(
        bootstrap_servers=settings.msk_bootstrap_servers,
        security_protocol="SASL_SSL",
        sasl_mechanism="OAUTHBEARER",
        sasl_oauth_token_provider=MSKTokenProvider(settings.msk_region),
        ssl_context=ssl_context,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    await producer.start()
    try:
        count = 0
        for user_data in users:
            key = str(user_data.get("id", "")).encode("utf-8")
            await producer.send_and_wait(settings.msk_topic, value=user_data, key=key)
            count += 1
        logger.info("Exported %d user(s) to MSK topic '%s'", count, settings.msk_topic)
        return count
    finally:
        await producer.stop()
