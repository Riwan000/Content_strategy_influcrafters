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

def parse_calendar_output(output_text, posting_frequency):
    weeks = []
    
    try:
        # First try splitting by weeks
        week_sections = re.split(r"Week\s*(\d+):", output_text, flags=re.IGNORECASE)
        
        # If no weeks found, try to parse as single week
        if len(week_sections) < 3:
            week_sections = ["", "1", output_text]
        
        for i in range(1, len(week_sections), 2):
            if i + 1 >= len(week_sections):
                print(f"[WARNING] Incomplete week section at index {i}")
                continue
                
            try:
                week_num = int(week_sections[i])
                week_content = week_sections[i+1]
                week = {"week": week_num, "posts": []}
                
                # Split posts by day markers with more flexible matching
                post_blocks = re.split(r"Day\s*\d+\s*-\s*Post:|Day\s*\d+:|Post\s*\d+:", week_content)
                
                # Ensure we have exactly posting_frequency posts per week
                if len(post_blocks[1:]) != posting_frequency:
                    print(f"[WARNING] Expected {posting_frequency} posts but found {len(post_blocks[1:])} in week {week_num}")
                    
                for post_block in post_blocks[1:]:  # Skip first empty block
                    try:
                        # Extract all fields with more flexible matching
                        day = re.search(r"🗓\s*Day:\s*(.+?)(\n|$)|Day:\s*(.+?)(\n|$)", post_block)
                        post_type = re.search(r"📌\s*Type:\s*(.+?)(\n|$)|Type:\s*(.+?)(\n|$)", post_block)
                        theme = re.search(r"🎯\s*Theme:\s*(.+?)(\n|$)|Theme:\s*(.+?)(\n|$)", post_block)
                        caption = re.search(r"✍️\s*Caption:\s*([\s\S]+?)(?=\n🏷|\nHashtags:|$)|Caption:\s*([\s\S]+?)(?=\n🏷|\nHashtags:|$)", post_block)
                        hashtags = re.search(r"🏷\s*Hashtags:\s*(.+?)(\n|$)|Hashtags:\s*(.+?)(\n|$)", post_block)
                        
                        # Extract the first matching group from each regex
                        day_text = next((g for g in (day.groups() if day else []) if g and g.strip()), "N/A")
                        post_type_text = next((g for g in (post_type.groups() if post_type else []) if g and g.strip()), "N/A")
                        theme_text = next((g for g in (theme.groups() if theme else []) if g and g.strip()), "N/A")
                        caption_text = next((g for g in (caption.groups() if caption else []) if g and g.strip()), "N/A")
                        hashtags_text = next((g for g in (hashtags.groups() if hashtags else []) if g and g.strip()), "")
                        
                        week["posts"].append({
                            "day": day_text.strip(),
                            "post_type": post_type_text.strip(),
                            "theme": theme_text.strip(),
                            "caption": caption_text.strip(),
                            "hashtags": [h.strip() for h in hashtags_text.split(',')] if hashtags_text else []
                        })
                    except Exception as e:
                        print(f"[WARNING] Error parsing post block: {str(e)}")
                        # Add a placeholder post if parsing fails
                        week["posts"].append({
                            "day": "N/A",
                            "post_type": "N/A",
                            "theme": "N/A",
                            "caption": "Error parsing post",
                            "hashtags": []
                        })
                
                weeks.append(week)
            except Exception as e:
                print(f"[WARNING] Error parsing week {i}: {str(e)}")
    except Exception as e:
        print(f"[ERROR] Failed to parse calendar output: {str(e)}")
        # Return a minimal valid structure
        return [{"week": 1, "posts": [{"day": "N/A", "post_type": "N/A", "theme": "N/A", "caption": "Error parsing calendar", "hashtags": []}]}]
    
    # If no weeks were parsed, return a minimal valid structure
    if not weeks:
        print("[WARNING] No weeks parsed, returning minimal structure")
        return [{"week": 1, "posts": [{"day": "N/A", "post_type": "N/A", "theme": "N/A", "caption": "No content generated", "hashtags": []}]}]
    
    return weeks

async def generate_calendar(
    brand_name: str,
    niche: str,
    platform: str,
    posting_frequency: int,
    tone: str,
    db: AsyncSession = Depends(get_db)
):
    print(f"[DEBUG] Generating calendar for {brand_name}")
    prompt = f"""
You are a social media strategist.

Generate a 4-week content calendar for a brand named '{brand_name}' in the '{niche}' niche, for the '{platform}' platform, with exactly {posting_frequency} posts per week (one for each day specified), using a '{tone}' brand voice.

For each post, provide the following details:
🗓 Day: [Day Number]
📌 Type: [Post Type, e.g., Post, Reel, Story, Question, Image/Gif, Longform Post/Carousel]
🎯 Theme: [Theme of the post]
✍️ Caption: [Engaging caption for the post]
🏷 Hashtags: [Relevant hashtags, comma-separated]

Break it down by week, with exactly {posting_frequency} posts per week (one for each day specified). Ensure all fields are filled with relevant information. If a field is not applicable, use 'N/A'.

Example format for {posting_frequency} posts per week:
Week 1:
Day 1 - Post:
🗓 Day: Day 1
📌 Type: Post
🎯 Theme: Introduction to Data Science
✍️ Caption: 💡 Dive into the world of Data Science! Today we kick off our journey with the basics. 📈 What's your first question? Ask away!
🏷 Hashtags: #DataScienceForAll, #LetsLearnTogether

Day 2 - Post:
🗓 Day: Day 2
📌 Type: Reel
🎯 Theme: Data Visualization Basics
✍️ Caption: 📊 Seeing is understanding! Today we explore simple data visualization techniques. What's your favorite chart type?
🏷 Hashtags: #DataViz, #LearnWithMe

[Continue with {posting_frequency} posts per week]

Now, generate the 4-week content calendar with exactly {posting_frequency} posts per week:
"""
    print(f"[DEBUG] Generated prompt: {prompt[:200]}...")  # Log first 200 chars of prompt
    try:
        print("[DEBUG] Calling OpenRouter API")
        output_text = await call_openrouter_api(prompt, max_tokens=4000)
        print(f"[DEBUG] Received API response: {output_text[:200]}...")  # Log first 200 chars
        calendar_struct = parse_calendar_output(output_text, posting_frequency)
        print(f"[DEBUG] Parsed calendar structure: {calendar_struct}")
    except Exception as e:
        print(f"[ERROR] Failed to generate calendar: {str(e)}")
        raise
    # Validate we got the correct number of posts per week
    if not isinstance(calendar_struct, list):
        print(f"[ERROR] Invalid calendar structure: {type(calendar_struct)}")
        return []
        
    for week in calendar_struct:
        if not isinstance(week, dict) or 'posts' not in week:
            print(f"[ERROR] Invalid week structure: {week}")
            continue
            
        if len(week.get('posts', [])) != posting_frequency:
            print(f"[ERROR] Week {week.get('week', '?')} has {len(week.get('posts', []))} posts, expected {posting_frequency}")
            # Don't regenerate, just continue with what we have
            continue
    
    # Store brand if not exists
    result = await db.execute(select(Brand).where(Brand.name == brand_name))
    brand = result.scalars().first()
    if not brand:
        brand = Brand(name=brand_name, niche=niche, tone=tone, platform=platform)
        db.add(brand)
        await db.commit()
        await db.refresh(brand)
    return calendar_struct