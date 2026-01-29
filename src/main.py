from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Cookie
from fastapi.responses import RedirectResponse
from src.strava import StravaService
import logging
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

strava_service = StravaService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await strava_service.postgres_service.initialize()
    yield
    await strava_service.postgres_service.close()


app = FastAPI(lifespan=lifespan)


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
