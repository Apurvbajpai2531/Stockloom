from sqlalchemy import Column, Integer, String, Text, Numeric, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(64), nullable=False, unique=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    unit = Column(String(30), nullable=False, default="pcs")
    unit_price = Column(Numeric(12, 2), nullable=False, default=0)
    reorder_threshold = Column(Integer, nullable=False, default=10)

    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    category = relationship("Category", back_populates="items")
    supplier = relationship("Supplier", back_populates="items")
    stock_levels = relationship("StockLevel", back_populates="item", cascade="all, delete-orphan")
    movements = relationship("StockMovement", back_populates="item", cascade="all, delete-orphan")
