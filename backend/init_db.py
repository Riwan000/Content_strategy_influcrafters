import asyncio
from backend.database import engine, Base
from backend.models import brand, content_calendar, competitor, trend, user

async def init_models():
    async with engine.begin() as conn:
        # Create tables with checkfirst=True
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Tables created.")

if __name__ == "__main__":
    asyncio.run(init_models()) 