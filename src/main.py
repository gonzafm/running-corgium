import logging
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Cookie, Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from src.config import settings
from src.database.activity_repository import ActivityRepository
from src.strava import StravaService

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def _create_activity_repo() -> ActivityRepository:
    if settings.db_backend == "dynamodb":
        import boto3

        from src.database.dynamo_service import DynamoService

        dynamodb = boto3.resource(
            "dynamodb",
            endpoint_url=settings.dynamodb_endpoint_url,
            region_name=settings.dynamodb_region,
        )
        return DynamoService(dynamodb.Table(settings.dynamodb_table_name))

    from src.database import PostgresService
    from src.database.db import get_session_maker

    return PostgresService(get_session_maker())


activity_repo = _create_activity_repo()
strava_service = StravaService(activity_repo)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.db_backend == "dynamodb":
        if not settings.is_lambda:
            from src.database.dynamo_service import ensure_dynamo_table

            await ensure_dynamo_table(
                settings.dynamodb_endpoint_url,
                settings.dynamodb_region,
                settings.dynamodb_table_name,
            )
    else:
        from src.database.db import create_db_and_tables

        await create_db_and_tables()

    await activity_repo.initialize()
    yield

    if settings.db_backend == "standalone":
        from src.database.db import get_engine

        await get_engine().dispose()


app = FastAPI(lifespan=lifespan)

logger = logging.getLogger("running-corgium")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info("%s %s", request.method, request.url.path)
    response = await call_next(request)
    logger.info("%s %s -> %d", request.method, request.url.path, response.status_code)
    return response


# --- Auth setup: standalone uses fastapi-users, aws uses API Gateway/Cognito ---
if settings.db_backend == "standalone":
    from src.auth import auth_backend, current_active_user, fastapi_users
    from src.auth.schemas import UserCreate, UserRead, UserUpdate
    from src.database.models import User

    app.include_router(
        fastapi_users.get_auth_router(auth_backend),
        prefix="/auth/jwt",
        tags=["auth"],
    )
    app.include_router(
        fastapi_users.get_register_router(UserRead, UserCreate),
        prefix="/auth",
        tags=["auth"],
    )
    app.include_router(
        fastapi_users.get_reset_password_router(),
        prefix="/auth",
        tags=["auth"],
    )
    app.include_router(
        fastapi_users.get_verify_router(UserRead),
        prefix="/auth",
        tags=["auth"],
    )
    app.include_router(
        fastapi_users.get_users_router(UserRead, UserUpdate),
        prefix="/users",
        tags=["users"],
    )

    @app.get("/authenticated-route")
    async def authenticated_route(user: User = Depends(current_active_user)):
        return {"message": f"Hello {user.email}!"}

    @app.get("/export/users", tags=["export"])
    async def export_users(user: User = Depends(current_active_user)):
        if not user.is_superuser:
            raise HTTPException(status_code=403, detail="Superuser required")

        from sqlalchemy import select

        from src.database.db import get_session_maker
        from src.export.kafka_producer import send_users_to_msk, serialize_user

        async with get_session_maker()() as session:
            result = await session.execute(select(User))
            users = result.scalars().all()

        serialized = [serialize_user(u) for u in users]
        count = await send_users_to_msk(serialized)
        return {"exported": count}

else:
    # AWS mode: extract user identity from API Gateway/Cognito request context
    async def _get_cognito_user(request: Request) -> dict[str, str]:
        # Mangum populates request context from API Gateway event
        claims: dict[str, str] = {}
        event = request.scope.get("aws.event", {})
        request_context = event.get("requestContext", {})
        authorizer = request_context.get("authorizer", {})
        if "claims" in authorizer:
            claims = authorizer["claims"]
        elif "jwt" in authorizer:
            claims = authorizer["jwt"].get("claims", {})

        if not claims:
            raise HTTPException(status_code=401, detail="Missing Cognito claims")

        return {
            "sub": claims.get("sub", ""),
            "email": claims.get("email", ""),
        }

    current_active_user = Depends(_get_cognito_user)

    @app.get("/users/me", tags=["users"])
    async def users_me(user: dict[str, str] = Depends(_get_cognito_user)):
        return {
            "id": 0,
            "email": user["email"],
            "is_active": True,
            "is_superuser": False,
            "is_verified": True,
        }


@app.get("/login/{name}")
async def login_user(name: str):
    redirect_url = strava_service.get_basic_info()
    session_id = str(uuid.uuid4())
    logging.info(f"Redirecting user {name} to Strava with session id {session_id}")
    response = RedirectResponse(url=redirect_url)
    response.set_cookie(
        key="session_id", value=session_id, httponly=True, samesite="lax"
    )
    return response


@app.get("/strava/authorize")
async def authorize(code: str, session_id: str = Cookie(None)):
    logging.info(f"Strava called back with code: {code}")
    try:
        await strava_service.authenticate_and_store(session_id, code)
        logging.info(f"Authorization successful for session {session_id}.")
        return RedirectResponse(url="/dashboard")
    except Exception as e:
        logging.error(f"Authorization failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/strava/athlete")
async def athlete(session_id: str = Cookie(None)):
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        return await strava_service.get_athlete(session_id)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@app.get("/strava/activities")
async def list_activities(session_id: str = Cookie(None)):
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        return await strava_service.list_activities(session_id)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


# --- SPA static files ---
_frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if _frontend_dist.is_dir():
    app.mount(
        "/assets", StaticFiles(directory=_frontend_dist / "assets"), name="static"
    )

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Serve actual files (e.g. vite.svg) if they exist
        file_path = _frontend_dist / full_path
        if full_path and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(_frontend_dist / "index.html")
