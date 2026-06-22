from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.stock import StockLevel, StockMovement, MovementType
from app.models.item import Item
from app.models.organization import Warehouse
from app.schemas.stock import StockMovementCreate, StockMovementOut, StockLevelOut

router = APIRouter()


def _get_or_create_level(db: Session, item_id: int, warehouse_id: int) -> StockLevel:
    level = (
        db.query(StockLevel)
        .filter(StockLevel.item_id == item_id, StockLevel.warehouse_id == warehouse_id)
        .first()
    )
    if not level:
        level = StockLevel(item_id=item_id, warehouse_id=warehouse_id, quantity=0)
        db.add(level)
        db.flush()
    return level


@router.get("/stock-levels", response_model=list[StockLevelOut])
def list_stock_levels(item_id: int | None = None, warehouse_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(StockLevel)
    if item_id:
        q = q.filter(StockLevel.item_id == item_id)
    if warehouse_id:
        q = q.filter(StockLevel.warehouse_id == warehouse_id)
    return q.all()


@router.get("/stock-movements", response_model=list[StockMovementOut])
def list_stock_movements(
    item_id: int | None = None,
    warehouse_id: int | None = None,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    q = db.query(StockMovement)
    if item_id:
        q = q.filter(StockMovement.item_id == item_id)
    if warehouse_id:
        q = q.filter(StockMovement.warehouse_id == warehouse_id)
    return q.order_by(StockMovement.created_at.desc()).limit(limit).all()


@router.post("/stock-movements", response_model=StockMovementOut, status_code=201)
def create_stock_movement(payload: StockMovementCreate, db: Session = Depends(get_db)):
    item = db.query(Item).get(payload.item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    warehouse = db.query(Warehouse).get(payload.warehouse_id)
    if not warehouse:
        raise HTTPException(status_code=404, detail="Source warehouse not found")

    source_level = _get_or_create_level(db, payload.item_id, payload.warehouse_id)

    if payload.movement_type == MovementType.INBOUND:
        source_level.quantity += payload.quantity

    elif payload.movement_type == MovementType.OUTBOUND:
        if source_level.quantity < payload.quantity:
            raise HTTPException(status_code=400, detail="Insufficient stock for outbound movement")
        source_level.quantity -= payload.quantity

    elif payload.movement_type == MovementType.TRANSFER:
        if not payload.destination_warehouse_id:
            raise HTTPException(status_code=400, detail="destination_warehouse_id is required for transfers")
        if payload.destination_warehouse_id == payload.warehouse_id:
            raise HTTPException(status_code=400, detail="Source and destination warehouses must differ")
        dest_wh = db.query(Warehouse).get(payload.destination_warehouse_id)
        if not dest_wh:
            raise HTTPException(status_code=404, detail="Destination warehouse not found")
        if source_level.quantity < payload.quantity:
            raise HTTPException(status_code=400, detail="Insufficient stock for transfer")
        source_level.quantity -= payload.quantity
        dest_level = _get_or_create_level(db, payload.item_id, payload.destination_warehouse_id)
        dest_level.quantity += payload.quantity

    elif payload.movement_type == MovementType.ADJUSTMENT:
        # Adjustment quantity represents the new absolute quantity at this warehouse
        source_level.quantity = payload.quantity

    movement = StockMovement(**payload.model_dump())
    db.add(movement)
    db.commit()
    db.refresh(movement)
    return movement
