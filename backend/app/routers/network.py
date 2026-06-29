from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func


from app.core.database import get_db
from app.models.organization import Warehouse
from app.models.stock import StockLevel, StockMovement, MovementType
from app.models.item import Item

router = APIRouter()


@router.get("/network/flow-graph")
def flow_graph(db: Session = Depends(get_db)):
    warehouses = db.query(Warehouse).all()
    stock_totals = dict(
        db.query(StockLevel.warehouse_id, func.coalesce(func.sum(StockLevel.quantity), 0))
        .group_by(StockLevel.warehouse_id)
        .all()
    )

    nodes = [
        {
            "id": w.id,
            "name": w.name,
            "code": w.code,
            "total_stock": int(stock_totals.get(w.id, 0)),
        }
        for w in warehouses
    ]

    edge_data = (
        db.query(
            StockMovement.warehouse_id,
            StockMovement.destination_warehouse_id,
            func.count(StockMovement.id),
            func.coalesce(func.sum(StockMovement.quantity), 0),
        )
        .filter(StockMovement.movement_type == MovementType.TRANSFER)
        .group_by(StockMovement.warehouse_id, StockMovement.destination_warehouse_id)
        .all()
    )

    edges = [
        {
            "from": src,
            "to": dst,
            "transfer_count": count,
            "total_quantity": int(qty),
        }
        for src, dst, count, qty in edge_data
        if dst is not None
    ]

    return {"nodes": nodes, "edges": edges}

@router.get("/network/pulse")
def system_pulse(db: Session = Depends(get_db)):
    """Aggregated health metrics for the animated pulse dashboard."""
    total_items = db.query(func.count(Item.id)).scalar() or 0
    total_warehouses = db.query(func.count(Warehouse.id)).scalar() or 0
    total_units = db.query(func.coalesce(func.sum(StockLevel.quantity), 0)).scalar() or 0

    totals_by_item = dict(
        db.query(StockLevel.item_id, func.coalesce(func.sum(StockLevel.quantity), 0))
        .group_by(StockLevel.item_id)
        .all()
    )
    low_count = 0
    for item in db.query(Item).all():
        if totals_by_item.get(item.id, 0) <= item.reorder_threshold:
            low_count += 1

    recent_transfers = (
        db.query(func.count(StockMovement.id))
        .filter(StockMovement.movement_type == MovementType.TRANSFER)
        .scalar()
        or 0
    )

    health_score = max(0, 100 - int((low_count / max(total_items, 1)) * 100))

    return {
        "health_score": health_score,
        "total_items": total_items,
        "total_warehouses": total_warehouses,
        "total_units": int(total_units),
        "low_stock_count": low_count,
        "recent_transfers": recent_transfers,
    }