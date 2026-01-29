import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import Cookie, Depends, FastAPI, HTTPException
from fastapi.responses import RedirectResponse

from src.auth import auth_backend, current_active_user, fastapi_users
from src.auth.schemas import UserCreate, UserRead, UserUpdate
from src.database.db import create_db_and_tables
from src.database.models import User
from src.strava import StravaService

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

strava_service = StravaService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    await strava_service.postgres_service.initialize()
    yield
    await strava_service.postgres_service.close()


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
