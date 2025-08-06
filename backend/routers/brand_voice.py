from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

class TextInput(BaseModel):
    text: str

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "mistralai/mistral-7b-instruct") # Default to Mistral

async def call_openrouter_api(prompt: str, max_tokens: int = 20):
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

@router.post("/analyze-tone")
async def analyze_tone(data: TextInput):
    prompt = f"""
You are a senior brand strategist.

Analyze the tone, voice, and emotional expression of the following caption in detail. Include stylistic choices, personality traits, emotional tone, and the brand archetype it represents.

Caption: "{data.text}"
"""
    result = await call_openrouter_api(
        prompt,
        max_tokens=300
    )
    return {"brand_voice_description": result}

@router.post("/analyze-tone")
def analyze_tone(data: TextInput):
    prompt = f"""
You are a senior brand strategist.

Analyze the tone, voice, and emotional expression of the following caption in detail. Include stylistic choices, personality traits, emotional tone, and the brand archetype it represents.

Caption: "{data.text}"
"""