from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.models.item import Item
from app.models.stock import StockLevel
from app.models.organization import Warehouse

router = APIRouter()


@router.get("/dashboard/summary")
def dashboard_summary(db: Session = Depends(get_db)):
    total_items = db.query(func.count(Item.id)).scalar() or 0
    total_warehouses = db.query(func.count(Warehouse.id)).scalar() or 0
    total_units = db.query(func.coalesce(func.sum(StockLevel.quantity), 0)).scalar() or 0
    total_value = (
        db.query(func.coalesce(func.sum(StockLevel.quantity * Item.unit_price), 0))
        .join(Item, Item.id == StockLevel.item_id)
        .scalar()
        or 0
    )

    totals_by_item = dict(
        db.query(StockLevel.item_id, func.coalesce(func.sum(StockLevel.quantity), 0))
        .group_by(StockLevel.item_id)
        .all()
    )
    low_stock_count = 0
    for item in db.query(Item).all():
        if totals_by_item.get(item.id, 0) <= item.reorder_threshold:
            low_stock_count += 1

    return {
        "total_items": total_items,
        "total_warehouses": total_warehouses,
        "total_units": int(total_units),
        "total_inventory_value": float(total_value),
        "low_stock_count": low_stock_count,
    }


@router.get("/dashboard/stock-by-warehouse")
def stock_by_warehouse(db: Session = Depends(get_db)):
    rows = (
        db.query(Warehouse.name, func.coalesce(func.sum(StockLevel.quantity), 0))
        .outerjoin(StockLevel, StockLevel.warehouse_id == Warehouse.id)
        .group_by(Warehouse.id, Warehouse.name)
        .order_by(Warehouse.name)
        .all()
    )
    return [{"warehouse": name, "quantity": int(qty)} for name, qty in rows]


@router.get("/dashboard/top-items")
def top_items_by_quantity(limit: int = 8, db: Session = Depends(get_db)):
    rows = (
        db.query(Item.name, func.coalesce(func.sum(StockLevel.quantity), 0).label("qty"))
        .outerjoin(StockLevel, StockLevel.item_id == Item.id)
        .group_by(Item.id, Item.name)
        .order_by(func.coalesce(func.sum(StockLevel.quantity), 0).desc())
        .limit(limit)
        .all()
    )
    return [{"name": name, "quantity": int(qty)} for name, qty in rows]
