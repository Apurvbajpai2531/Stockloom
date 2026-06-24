import time

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
        level = StockLevel(item_id=item_id, warehouse_id=warehouse_id, quantity=0, version=0)
        db.add(level)
        db.flush()
    return level


def _apply_with_lock(db: Session, level: StockLevel, delta_fn, max_retries: int = 3):
    """
    Optimistic concurrency: re-reads the row, applies delta_fn, and commits with a
    version check. If another transaction modified the row in between, retries.
    This is the same pattern banks/e-commerce systems use to avoid lost stock updates
    when two requests hit the same item+warehouse simultaneously.
    """
    for attempt in range(max_retries):
        current_version = level.version
        delta_fn(level)
        rows_updated = (
            db.query(StockLevel)
            .filter(StockLevel.id == level.id, StockLevel.version == current_version)
            .update({"quantity": level.quantity, "version": current_version + 1})
        )
        if rows_updated:
            db.flush()
            return True
        db.rollback()
        time.sleep(0.05 * (attempt + 1))
        db.refresh(level)
    raise HTTPException(status_code=409, detail="Stock update conflict — please retry (another change happened simultaneously)")


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
    if payload.idempotency_key:
        existing = db.query(StockMovement).filter(
            StockMovement.idempotency_key == payload.idempotency_key
        ).first()
        if existing:
            return existing  # already processed — return the original result, don't double-apply

    item = db.query(Item).get(payload.item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    warehouse = db.query(Warehouse).get(payload.warehouse_id)
    if not warehouse:
        raise HTTPException(status_code=404, detail="Source warehouse not found")

    source_level = _get_or_create_level(db, payload.item_id, payload.warehouse_id)

    if payload.movement_type == MovementType.INBOUND:
        _apply_with_lock(db, source_level, lambda lvl: setattr(lvl, "quantity", lvl.quantity + payload.quantity))

    elif payload.movement_type == MovementType.OUTBOUND:
        if source_level.quantity < payload.quantity:
            raise HTTPException(status_code=400, detail="Insufficient stock for outbound movement")
        _apply_with_lock(db, source_level, lambda lvl: setattr(lvl, "quantity", lvl.quantity - payload.quantity))

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
        _apply_with_lock(db, source_level, lambda lvl: setattr(lvl, "quantity", lvl.quantity - payload.quantity))
        dest_level = _get_or_create_level(db, payload.item_id, payload.destination_warehouse_id)
        _apply_with_lock(db, dest_level, lambda lvl: setattr(lvl, "quantity", lvl.quantity + payload.quantity))

    elif payload.movement_type == MovementType.ADJUSTMENT:
        _apply_with_lock(db, source_level, lambda lvl: setattr(lvl, "quantity", payload.quantity))

    movement = StockMovement(**payload.model_dump())
    db.add(movement)
    db.commit()
    db.refresh(movement)

    import asyncio
    from app.routers.ws import broadcast_stock_update
    try:
        asyncio.create_task(broadcast_stock_update({
            "type": "stock_movement",
            "item_id": movement.item_id,
            "movement_type": movement.movement_type.value,
            "quantity": movement.quantity,
        }))
    except Exception:
        pass

    return movement