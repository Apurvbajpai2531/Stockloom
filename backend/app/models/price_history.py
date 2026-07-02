from sqlalchemy import Column, Integer, ForeignKey, DateTime, Numeric, String
from sqlalchemy.sql import func
from app.core.database import Base


class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    old_price = Column(Numeric(12, 2), nullable=False)
    new_price = Column(Numeric(12, 2), nullable=False)
    changed_by = Column(String(80), nullable=True)
    changed_at = Column(DateTime(timezone=True), server_default=func.now())