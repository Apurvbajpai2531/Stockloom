from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, ConfigDict

from app.models.purchase_order import POStatus


class POLineCreate(BaseModel):
    item_id: int
    quantity_ordered: int
    unit_cost: Decimal = Decimal("0")


class POLineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    item_id: int
    quantity_ordered: int
    unit_cost: Decimal


class PurchaseOrderCreate(BaseModel):
    po_number: str
    supplier_id: Optional[int] = None
    warehouse_id: int
    notes: Optional[str] = None
    lines: List[POLineCreate]


class PurchaseOrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    po_number: str
    supplier_id: Optional[int] = None
    warehouse_id: int
    status: POStatus
    notes: Optional[str] = None
    created_at: datetime
    received_at: Optional[datetime] = None
    lines: List[POLineOut] = []