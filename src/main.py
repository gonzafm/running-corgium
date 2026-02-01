import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import Cookie, Depends, FastAPI, HTTPException
from fastapi.responses import RedirectResponse

from src.auth import auth_backend, current_active_user, fastapi_users
from src.auth.schemas import UserCreate, UserRead, UserUpdate
from src.config import settings
from src.database.activity_repository import ActivityRepository
from src.database.models import User
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
    from src.database.db import async_session_maker

    return PostgresService(async_session_maker)


activity_repo = _create_activity_repo()
strava_service = StravaService(activity_repo)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.db_backend == "dynamodb":
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

    if settings.db_backend == "postgres":
        from src.database.db import engine

        await engine.dispose()


app = FastAPI(lifespan=lifespan)

# --- Auth routers ---
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


@app.get("/login/{name}")
async def login_user(name: str):
    redirect_url = strava_service.get_basic_info()
    session_id = str(uuid.uuid4())
    logging.info(f"Redirecting user {name} to Strava with session id {session_id}")
    response = RedirectResponse(url=redirect_url)
    response.set_cookie(
        key="session_id", value=session_id, httponly=True, samesite="strict"
    )
    return response


@app.get("/strava/authorize")
async def authorize(code: str, session_id: str = Cookie(None)):
    logging.info(f"Strava called back with code: {code}")
    try:
        await strava_service.authenticate_and_store(session_id, code)
        logging.info(f"Authorization successful for session {session_id}.")
        return {"message": code}
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
