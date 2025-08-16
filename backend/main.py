import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file before anything else
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

from fastapi import FastAPI
from routers import brand_voice, competitor_scraper, trend_analyzer, calendar_generator, brands

app = FastAPI()

app.include_router(brand_voice.router)
app.include_router(competitor_scraper.router)
app.include_router(trend_analyzer.router)
app.include_router(calendar_generator.router)
app.include_router(brands.router)

@app.get("/ping")
def ping():
    return {"message": "pong"}