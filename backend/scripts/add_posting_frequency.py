"""
Simple migration: add posting_frequency column to brands table if it doesn't exist.
Run: python backend\scripts\add_posting_frequency.py
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load .env from project root
env_path = Path(__file__).resolve().parents[1] / '.env'
load_dotenv(dotenv_path=env_path)

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise SystemExit('DATABASE_URL not set in .env')

print('Using DATABASE_URL:', DATABASE_URL)
# If DATABASE_URL uses asyncpg dialect (postgresql+asyncpg), create a sync engine by switching to postgresql driver
sync_db_url = DATABASE_URL
if DATABASE_URL.startswith('postgresql+asyncpg://'):
    sync_db_url = DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')

engine = create_engine(sync_db_url)

with engine.begin() as conn:
    print('Running ALTER TABLE to add posting_frequency if missing...')
    conn.execute(text(
        "ALTER TABLE IF EXISTS brands ADD COLUMN IF NOT EXISTS posting_frequency INTEGER DEFAULT 3"
    ))

print('Done.')
