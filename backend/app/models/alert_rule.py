from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base


class AlertRule(Base):
    __tablename__ = "alert_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=True)  # None = all items
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=True)  # None = all warehouses
    condition = Column(String(20), nullable=False)  # "below", "above", "equals"
    threshold = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    created_by = Column(String(80), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())