import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request

from src.config import settings
from src.deployment import get_factory
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


def create_app() -> FastAPI:
    factory = get_factory(settings.db_backend)
    activity_repo = factory.create_repo()
    strava_service = StravaService(activity_repo)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await factory.init_db()
        await activity_repo.initialize()
        yield
        await factory.shutdown()

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

    factory.register_auth_routes(app)
    app.include_router(create_strava_router(strava_service))

    _frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
    register_spa_routes(app, _frontend_dist)

    return app


app = create_app()