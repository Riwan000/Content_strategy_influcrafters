import random
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from models.brand import Brand
from models.content_calendar import ContentCalendar
from database import get_db
from sqlalchemy.future import select
from fastapi import Depends
import re
import httpx
import os

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "mistralai/mistral-7b-instruct") # Default to Mistral

async def call_openrouter_api(prompt: str, max_tokens: int = 200):
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY environment variable not set.")

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 40,
        "repetition_penalty": 1.1 # OpenRouter uses repetition_penalty instead of repeat_penalty
    }

    async with httpx.AsyncClient() as client:
        response = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status() # Raise an exception for 4xx or 5xx status codes
        return response.json()["choices"][0]["message"]["content"].strip()

def parse_calendar_output(output_text):
    weeks = []
    week_blocks = re.split(r"Week\s*\d+[:\-]", output_text, flags=re.IGNORECASE)
    week_numbers = re.findall(r"Week\s*(\d+)", output_text, flags=re.IGNORECASE)
    for i, block in enumerate(week_blocks[1:]):  # skip the first split (before Week 1)
        week = {"week": int(week_numbers[i]), "posts": []}
        for line in block.strip().splitlines():
            if line.strip():
                week["posts"].append({
                    "day": f"Day {len(week['posts'])+1}",
                    "post_type": "Post",
                    "theme": line.strip(),
                    "caption": line.strip(),
                    "hashtags": []
                })
        weeks.append(week)
    return weeks

async def generate_calendar(
    brand_name: str,
    niche: str,
    platform: str,
    posting_frequency: int,
    tone: str,
    db: AsyncSession = Depends(get_db)
):
    prompt = f"""
You are a social media strategist.

Generate a 4-week content calendar for a brand named '{brand_name}' in the '{niche}' niche, for the '{platform}' platform, with a posting frequency of {posting_frequency} posts per week, using a '{tone}' brand voice.\n\nBreak it down by week, with 2-3 content ideas per week. Make it clear and actionable.
"""
    output_text = await call_openrouter_api(prompt, max_tokens=250)
    calendar_struct = parse_calendar_output(output_text)
    # Store brand if not exists
    result = await db.execute(select(Brand).where(Brand.name == brand_name))
    brand = result.scalars().first()
    if not brand:
        brand = Brand(name=brand_name, niche=niche, tone=tone, platform=platform)
        db.add(brand)
        await db.commit()
        await db.refresh(brand)
    return calendar_struct