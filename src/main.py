import logging
from contextlib import asynccontextmanager
from enum import StrEnum
from pathlib import Path
from abc import ABC, abstractmethod

from fastapi import FastAPI, Request

from src.config import settings
from src.database.activity_repository import ActivityRepository
from src.routers.frontend import register_spa_routes
from src.routers.strava import create_strava_router
from src.strava import StravaService

# Configure logging — force=True so it takes effect even in Lambda
# (where the runtime may have already configured the root logger)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    force=True,
)
logger = logging.getLogger("running-corgium")


class DeploymentMode(StrEnum):
    AWS = "aws"
    STANDALONE = "standalone"


class DeploymentFactory(ABC):
    @abstractmethod
    def create_service(self) -> ActivityRepository: ...

    @abstractmethod
    async def init_db(self) -> None: ...

    @abstractmethod
    async def post_db_init(self) -> None: ...

    @abstractmethod
    def decorate_router(self, application: FastAPI) -> None: ...


class AWSFactory(DeploymentFactory):
    def create_service(self) -> ActivityRepository:
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

    async def post_db_init(self) -> None:
        pass

    def decorate_router(self, application: FastAPI) -> None:
        from src.auth.cognito_routes import router as cognito_router

        application.include_router(cognito_router)


class StandaloneFactory(DeploymentFactory):
    def create_service(self) -> ActivityRepository:
        from src.database import PostgresService
        from src.database.db import get_session_maker

        return PostgresService(get_session_maker())

    async def init_db(self) -> None:
        from src.database.db import create_db_and_tables

        await create_db_and_tables()

    async def post_db_init(self) -> None:
        from src.database.db import get_engine

        await get_engine().dispose()

    def decorate_router(self, application: FastAPI) -> None:
        from src.auth.standalone_routes import register_standalone_auth_routes, router

        register_standalone_auth_routes(application)
        application.include_router(router)


_FACTORIES: dict[DeploymentMode, type[DeploymentFactory]] = {
    DeploymentMode.AWS: AWSFactory,
    DeploymentMode.STANDALONE: StandaloneFactory,
}


def create_app() -> FastAPI:
    factory = _FACTORIES[DeploymentMode(settings.db_backend)]()
    activity_repo = factory.create_service()
    strava_service = StravaService(activity_repo)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await factory.init_db()
        await activity_repo.initialize()
        yield
        await factory.post_db_init()

    app = FastAPI(lifespan=lifespan)
    app.state.strava_service = strava_service

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        logger.info("%s %s", request.method, request.url.path)
        response = await call_next(request)
        logger.info(
            "%s %s -> %d", request.method, request.url.path, response.status_code
        )
        return response

    # --- Register auth routes based on deployment mode ---
    factory.decorate_router(app)

    # --- Register Strava routes ---
    app.include_router(create_strava_router(strava_service))

    # --- Register SPA frontend routes ---
    _frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
    register_spa_routes(app, _frontend_dist)

    return app


app = create_app()
