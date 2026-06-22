from typing import Optional
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ItemBase(BaseModel):
    sku: str
    name: str
    description: Optional[str] = None
    unit: str = "pcs"
    unit_price: Decimal = Decimal("0")
    reorder_threshold: int = 10
    category_id: Optional[int] = None
    supplier_id: Optional[int] = None


class ItemCreate(ItemBase):
    pass


class ItemUpdate(BaseModel):
    sku: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    unit: Optional[str] = None
    unit_price: Optional[Decimal] = None
    reorder_threshold: Optional[int] = None
    category_id: Optional[int] = None
    supplier_id: Optional[int] = None


class ItemOut(ItemBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime


class ItemWithStock(ItemOut):
    total_quantity: int = 0
