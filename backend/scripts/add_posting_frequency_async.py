"""
Add posting_frequency column to brands table using asyncpg.
Run from project backend folder: python scripts\add_posting_frequency_async.py
"""
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
import asyncpg

# Load .env from project root
env_path = Path(__file__).resolve().parents[1] / '.env'
load_dotenv(dotenv_path=env_path)

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise SystemExit('DATABASE_URL not set in .env')

async def main():
    dsn = DATABASE_URL
    if dsn.startswith('postgresql+asyncpg://'):
        dsn = dsn.replace('postgresql+asyncpg://', 'postgresql://')
    print('Connecting to:', dsn)
    conn = await asyncpg.connect(dsn)
    try:
        print('Running ALTER TABLE to add posting_frequency if missing...')
        await conn.execute('ALTER TABLE IF EXISTS brands ADD COLUMN IF NOT EXISTS posting_frequency INTEGER DEFAULT 3')
        print('Migration complete.')
    finally:
        await conn.close()

if __name__ == '__main__':
    asyncio.run(main())
