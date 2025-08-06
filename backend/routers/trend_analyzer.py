from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.trend_analyzer import analyze_trends

router = APIRouter()

class AnalyzeTrendsRequest(BaseModel):
    keyword: str

@router.post("/analyze-trends")
def analyze_trends_endpoint(request: AnalyzeTrendsRequest):
    if not request.keyword:
        raise HTTPException(status_code=400, detail="'keyword' must be provided.")
    result = analyze_trends(request.keyword)
    return result