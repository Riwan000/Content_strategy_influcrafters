import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSON
from database import Base

class Trend(Base):
    __tablename__ = "trends"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id"))
    keyword = Column(String, nullable=False)
    related_topics = Column(JSON)
    rising_trends = Column(JSON)
    interest_over_time = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow) 