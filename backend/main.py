from fastapi import FastAPI
from routers import brand_voice, competitor_scraper, trend_analyzer, calendar_generator

app = FastAPI()

app.include_router(brand_voice.router)
app.include_router(competitor_scraper.router)
app.include_router(trend_analyzer.router)
app.include_router(calendar_generator.router)

@app.get("/ping")
def ping():
    return {"message": "pong"}