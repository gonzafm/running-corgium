from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from src.strava import StravaService
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app = FastAPI()
strava_service = StravaService()
tokens = dict()


@app.get("/login/{name}")
async def say_hello(name: str):
    redirect_url = strava_service.get_basic_info()
    return RedirectResponse(url=redirect_url)


@app.get("/strava/authorize")
async def authorize(code: str):
    logging.info(f"Strava called back with code: {code}")
    tokens["Gonzalo"] = str
    strava_service.authenticate_and_store(code)
    return {"message": code}


@app.get("/strava/athlete")
async def athlete():
    return strava_service.get_athlete()
