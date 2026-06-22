from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_validator

from app.models.stock import MovementType


class StockLevelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    item_id: int
    warehouse_id: int
    quantity: int
    updated_at: datetime


class StockMovementCreate(BaseModel):
    item_id: int
    warehouse_id: int
    movement_type: MovementType
    quantity: int
    destination_warehouse_id: Optional[int] = None
    reference: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("quantity")
    @classmethod
    def quantity_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("quantity must be a positive integer")
        return v


class StockMovementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    item_id: int
    warehouse_id: int
    destination_warehouse_id: Optional[int] = None
    movement_type: MovementType
    quantity: int
    reference: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
