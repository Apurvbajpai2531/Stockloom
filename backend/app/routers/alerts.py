from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.models.item import Item
from app.models.stock import StockLevel

router = APIRouter()


@router.get("/alerts/low-stock")
def low_stock_alerts(db: Session = Depends(get_db)):
    totals = dict(
        db.query(StockLevel.item_id, func.coalesce(func.sum(StockLevel.quantity), 0))
        .group_by(StockLevel.item_id)
        .all()
    )
    alerts = []
    for item in db.query(Item).all():
        qty = totals.get(item.id, 0)
        if qty <= item.reorder_threshold:
            severity = "critical" if qty == 0 else "warning"
            alerts.append({
                "item_id": item.id,
                "sku": item.sku,
                "name": item.name,
                "current_quantity": qty,
                "reorder_threshold": item.reorder_threshold,
                "severity": severity,
            })
    alerts.sort(key=lambda a: a["current_quantity"])
    return {"count": len(alerts), "alerts": alerts}