import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSON
from database import Base

class ContentCalendar(Base):
    __tablename__ = "calendars"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id"))
    week = Column(Integer)
    posts = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)