"""Deployment factory abstraction for standalone and AWS modes."""

from abc import ABC, abstractmethod
from enum import StrEnum

from fastapi import FastAPI

from src.config import settings
from src.database.activity_repository import ActivityRepository


class DeploymentMode(StrEnum):
    AWS = "aws"
    STANDALONE = "standalone"


class DeploymentFactory(ABC):
    @abstractmethod
    def create_repo(self) -> ActivityRepository: ...

    @abstractmethod
    async def init_db(self) -> None: ...

    @abstractmethod
    async def shutdown(self) -> None: ...

    @abstractmethod
    def register_auth_routes(self, application: FastAPI) -> None: ...


class AWSFactory(DeploymentFactory):
    def create_repo(self) -> ActivityRepository:
        import boto3

        from src.database.dynamo_service import DynamoService

        dynamodb = boto3.resource(
            "dynamodb",
            endpoint_url=settings.dynamodb_endpoint_url,
            region_name=settings.dynamodb_region,
        )
        return DynamoService(dynamodb.Table(settings.dynamodb_table_name))

    async def init_db(self) -> None:
        from src.database.dynamo_service import ensure_dynamo_table

        if settings.is_lambda:
            return
        await ensure_dynamo_table(
            settings.dynamodb_endpoint_url,
            settings.dynamodb_region,
            settings.dynamodb_table_name,
        )

    async def shutdown(self) -> None:
        pass

    def register_auth_routes(self, application: FastAPI) -> None:
        from src.auth.cognito_routes import router as cognito_router

        application.include_router(cognito_router)


class StandaloneFactory(DeploymentFactory):
    def create_repo(self) -> ActivityRepository:
        from src.database import PostgresService
        from src.database.db import get_session_maker

        return PostgresService(get_session_maker())

    async def init_db(self) -> None:
        from src.database.db import create_db_and_tables

        await create_db_and_tables()

    async def shutdown(self) -> None:
        from src.database.db import get_engine

        await get_engine().dispose()

    def register_auth_routes(self, application: FastAPI) -> None:
        from src.auth.standalone_routes import register_standalone_auth_routes, router

        register_standalone_auth_routes(application)
        application.include_router(router)


_FACTORIES: dict[DeploymentMode, type[DeploymentFactory]] = {
    DeploymentMode.AWS: AWSFactory,
    DeploymentMode.STANDALONE: StandaloneFactory,
}


def get_factory(db_backend: str) -> DeploymentFactory:
    """Create the appropriate factory for the given db_backend value."""
    return _FACTORIES[DeploymentMode(db_backend)]()