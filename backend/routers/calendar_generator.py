from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, EmailStr
from services.calendar_generator import generate_calendar
from database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from services import email_sender

router = APIRouter()

class CalendarRequest(BaseModel):
    brand_name: str
    niche: str
    platform: str
    posting_frequency: int
    tone: str

class EmailCalendarRequest(BaseModel):
    email: EmailStr
    calendar: list

@router.post("/generate-calendar")
async def generate_calendar_endpoint(
    request: CalendarRequest,
    db: AsyncSession = Depends(get_db)
):
    if not all([request.brand_name, request.niche, request.platform, request.posting_frequency, request.tone]):
        raise HTTPException(status_code=400, detail="All fields must be provided.")
    result = await generate_calendar(
        brand_name=request.brand_name,
        niche=request.niche,
        platform=request.platform,
        posting_frequency=request.posting_frequency,
        tone=request.tone,
        db=db
    )
    return result

@router.post("/email-calendar")
async def email_calendar(
    request: EmailCalendarRequest
):
    print("[DEBUG] /email-calendar endpoint called")
    try:
        def calendar_to_text(calendar):
            lines = []
            for week in calendar:
                lines.append(f"Week {week['week']}")
                for post in week['posts']:
                    lines.append(f"  {post['day']} - {post['post_type']} - {post['theme']}")
                    lines.append(f"    Caption: {post['caption']}")
                    lines.append(f"    Hashtags: {' '.join(post.get('hashtags', []))}")
                lines.append("")
            return '\n'.join(lines)
        text_body = calendar_to_text(request.calendar)
        subject = "Your Content Calendar"
        print(f"[DEBUG] Attempting to send email to {request.email}")
        email_sender.send_email(request.email, subject, text_body)
        print(f"[DEBUG] Email send function completed for {request.email}")
        return {"message": "Email sent (if successful)"}
    except Exception as e:
        print(f"[ERROR] Exception in /email-calendar: {e}")
        return {"error": str(e)}