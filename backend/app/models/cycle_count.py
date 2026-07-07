from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class CycleCount(Base):
    __tablename__ = "cycle_counts"

    id = Column(Integer, primary_key=True, index=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    status = Column(String(20), nullable=False, default="open")  # open, completed
    created_by = Column(String(80), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    warehouse = relationship("Warehouse")
    lines = relationship(
        "CycleCountLine", back_populates="cycle_count", cascade="all, delete-orphan"
    )


class CycleCountLine(Base):
    __tablename__ = "cycle_count_lines"

    id = Column(Integer, primary_key=True, index=True)
    cycle_count_id = Column(Integer, ForeignKey("cycle_counts.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    system_quantity = Column(Integer, nullable=False)
    counted_quantity = Column(Integer, nullable=True)
    variance = Column(Integer, nullable=True)
    is_verified = Column(Boolean, default=False)

    cycle_count = relationship("CycleCount", back_populates="lines")
    item = relationship("Item")
