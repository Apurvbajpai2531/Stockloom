from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func

from app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(50), nullable=False)       # e.g. "create_item", "delete_warehouse"
    entity_type = Column(String(50), nullable=False)   # e.g. "item", "warehouse"
    entity_id = Column(Integer, nullable=True)
    username = Column(String(80), nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
