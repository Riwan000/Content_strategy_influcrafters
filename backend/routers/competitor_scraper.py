from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.competitor_scraper import scrape_competitor

router = APIRouter()

class ScrapeCompetitorRequest(BaseModel):
    url: str

@router.post("/scrape-competitor")
def scrape_competitor_endpoint(request: ScrapeCompetitorRequest):
    if not request.url:
        raise HTTPException(status_code=400, detail="'url' must be provided.")
    result = scrape_competitor(request.url)
    return result