import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSON
from database import Base

class Competitor(Base):
    __tablename__ = "competitors"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id"))
    name = Column(String, nullable=False)
    insights = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow) 