"""Strava integration endpoints."""

import logging
import uuid

from fastapi import APIRouter, Cookie, HTTPException
from fastapi.responses import RedirectResponse

from src.strava import StravaService

router = APIRouter()
logger = logging.getLogger(__name__)


def create_strava_router(strava_service: StravaService) -> APIRouter:
    """Create a router with Strava endpoints bound to a service instance."""

    @router.get("/login/{name}")
    async def login_user(name: str):
        redirect_url = strava_service.get_basic_info()
        session_id = str(uuid.uuid4())
        logger.info(
            "Redirecting user %s to Strava with session id %s", name, session_id
        )
        response = RedirectResponse(url=redirect_url)
        response.set_cookie(
            key="session_id", value=session_id, httponly=True, samesite="lax"
        )
        return response

    @router.get("/strava/authorize")
    async def authorize(code: str, session_id: str = Cookie(None)):
        logger.info("Strava called back with code: %s", code)
        try:
            await strava_service.authenticate_and_store(session_id, code)
            logger.info("Authorization successful for session %s.", session_id)
            return RedirectResponse(url="/dashboard")
        except Exception as e:
            logger.error("Authorization failed: %s", e)
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/strava/athlete")
    async def athlete(session_id: str = Cookie(None)):
        if not session_id:
            raise HTTPException(status_code=401, detail="Not authenticated")
        try:
            return await strava_service.get_athlete(session_id)
        except ValueError as e:
            raise HTTPException(status_code=401, detail=str(e))

    @router.get("/strava/activities")
    async def list_activities(session_id: str = Cookie(None)):
        if not session_id:
            raise HTTPException(status_code=401, detail="Not authenticated")
        try:
            return await strava_service.list_activities(session_id)
        except ValueError as e:
            raise HTTPException(status_code=401, detail=str(e))

    return router
