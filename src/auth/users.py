import logging
from collections.abc import AsyncGenerator

from fastapi import Depends
from fastapi_users import BaseUserManager, FastAPIUsers, IntegerIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase

from src.config import settings
from src.database.db import get_user_db
from src.database.models import User

logger = logging.getLogger(__name__)


class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    reset_password_token_secret = settings.jwt_secret.get_secret_value()
    verification_token_secret = settings.jwt_secret.get_secret_value()

    async def on_after_register(
        self, user: User, request: object | None = None
    ) -> None:
        logger.info("User %d has registered.", user.id)

    async def on_after_forgot_password(
        self, user: User, token: str, request: object | None = None
    ) -> None:
        logger.info("User %d has requested a password reset.", user.id)

    async def on_after_request_verify(
        self, user: User, token: str, request: object | None = None
    ) -> None:
        logger.info("Verification requested for user %d. Token: %s", user.id, token)


async def get_user_manager(
    user_db: SQLAlchemyUserDatabase[User, int] = Depends(get_user_db),
) -> AsyncGenerator[UserManager]:
    yield UserManager(user_db)


bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")


def get_jwt_strategy() -> JWTStrategy[User, int]:
    return JWTStrategy(
        secret=settings.jwt_secret.get_secret_value(),
        lifetime_seconds=settings.jwt_lifetime_seconds,
    )


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, int](get_user_manager, [auth_backend])

current_active_user = fastapi_users.current_user(active=True)
