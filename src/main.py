from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from src.strava import StravaService
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app = FastAPI()
strava_service = StravaService()
tokens: dict[str, str] = {}


@app.get("/login/{name}")
async def login_user(name: str):
    redirect_url = strava_service.get_basic_info()
    return RedirectResponse(url=redirect_url)


@app.get("/strava/authorize")
async def authorize(code: str):
    logging.info(f"Strava called back with code: {code}")
    try:
        strava_service.authenticate_and_store(code)
        logging.info("Authorization successful")
        return {"message": code}
    except Exception as e:
        logging.error(f"Authorization failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/strava/athlete")
async def athlete():
    return strava_service.get_athlete()
