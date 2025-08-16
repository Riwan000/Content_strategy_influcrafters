from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models.brand import Brand
from sqlalchemy import select

router = APIRouter()

class BrandCreate(BaseModel):
    name: str
    niche: str | None = None
    tone: str | None = None
    platform: str | None = None
    posting_frequency: int | None = 3

class BrandOut(BaseModel):
    id: str
    name: str
    niche: str | None
    tone: str | None
    platform: str | None
    posting_frequency: int | None

    @classmethod
    def from_orm(cls, obj):
        # Convert UUID to string for id
        return cls(
            id=str(obj.id),
            name=obj.name,
            niche=obj.niche,
            tone=obj.tone,
            platform=obj.platform,
            posting_frequency=obj.posting_frequency
        )

@router.post("/brands", response_model=BrandOut)
async def create_brand(brand: BrandCreate, db: AsyncSession = Depends(get_db)):
    new_brand = Brand(
        name=brand.name,
        niche=brand.niche,
        tone=brand.tone,
        platform=brand.platform,
        posting_frequency=brand.posting_frequency or 3
    )
    db.add(new_brand)
    await db.commit()
    await db.refresh(new_brand)
    return BrandOut.from_orm(new_brand)

@router.get("/brands", response_model=list[BrandOut])
async def list_brands(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Brand))
    brands = result.scalars().all()
    return [BrandOut.from_orm(b) for b in brands]
