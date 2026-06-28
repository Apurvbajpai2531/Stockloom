from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.models.organization import Warehouse
from app.models.stock import StockLevel, StockMovement, MovementType

router = APIRouter()


@router.get("/network/flow-graph")
def flow_graph(db: Session = Depends(get_db)):
    """
    Returns warehouses as nodes (with total stock) and recent transfers as edges
    (with transfer counts/volume) — used to draw the live stock flow visualization.
    """
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

    return {"nodes": nodes, "edges": edges}from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.models.organization import Warehouse
from app.models.stock import StockLevel, StockMovement, MovementType

router = APIRouter()


@router.get("/network/flow-graph")
def flow_graph(db: Session = Depends(get_db)):
    """
    Returns warehouses as nodes (with total stock) and recent transfers as edges
    (with transfer counts/volume) — used to draw the live stock flow visualization.
    """
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