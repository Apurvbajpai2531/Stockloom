from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.models.item import Item
from app.models.stock import StockLevel, StockMovement, MovementType
from app.models.organization import Warehouse
from app.models.purchase_order import PurchaseOrder

router = APIRouter()


@router.get("/analytics/scorecard")
def scorecard(db: Session = Depends(get_db)):
    """KPIs with period-over-period comparison (this week vs last week)."""
    now = datetime.now(timezone.utc)
    this_week = now - timedelta(days=7)
    last_week = now - timedelta(days=14)

    def movement_count(start, end, mtype):
        return (
            db.query(func.count(StockMovement.id))
            .filter(
                StockMovement.movement_type == mtype,
                StockMovement.created_at >= start,
                StockMovement.created_at < end,
            )
            .scalar() or 0
        )

    def movement_qty(start, end, mtype):
        return (
            db.query(func.coalesce(func.sum(StockMovement.quantity), 0))
            .filter(
                StockMovement.movement_type == mtype,
                StockMovement.created_at >= start,
                StockMovement.created_at < end,
            )
            .scalar() or 0
        )

    inbound_this = int(movement_qty(this_week, now, MovementType.INBOUND))
    inbound_last = int(movement_qty(last_week, this_week, MovementType.INBOUND))
    outbound_this = int(movement_qty(this_week, now, MovementType.OUTBOUND))
    outbound_last = int(movement_qty(last_week, this_week, MovementType.OUTBOUND))
    transfer_this = int(movement_count(this_week, now, MovementType.TRANSFER))
    transfer_last = int(movement_count(last_week, this_week, MovementType.TRANSFER))

    total_value = float(
        db.query(func.coalesce(func.sum(StockLevel.quantity * Item.unit_price), 0))
        .join(Item, Item.id == StockLevel.item_id)
        .scalar() or 0
    )
    open_pos = db.query(func.count(PurchaseOrder.id)).filter(
        PurchaseOrder.status.in_(["draft", "ordered"])
    ).scalar() or 0

    totals = dict(
        db.query(StockLevel.item_id, func.coalesce(func.sum(StockLevel.quantity), 0))
        .group_by(StockLevel.item_id)
        .all()
    )
    low_count = sum(1 for item in db.query(Item).all() if totals.get(item.id, 0) <= item.reorder_threshold)

    def trend(current, previous):
        if previous == 0:
            return "new" if current > 0 else "flat"
        pct = ((current - previous) / previous) * 100
        if pct > 5:
            return f"+{pct:.0f}%"
        elif pct < -5:
            return f"{pct:.0f}%"
        return "flat"

    return [
        {"label": "Units Inbound (7d)", "value": inbound_this, "trend": trend(inbound_this, inbound_last), "icon": "download", "color": "#2F6F6B"},
        {"label": "Units Outbound (7d)", "value": outbound_this, "trend": trend(outbound_this, outbound_last), "icon": "upload", "color": "#E8A33D"},
        {"label": "Transfers (7d)", "value": transfer_this, "trend": trend(transfer_this, transfer_last), "icon": "swap_horiz", "color": "#2563eb"},
        {"label": "Inventory Value", "value": f"${total_value:,.0f}", "trend": "", "icon": "payments", "color": "#2F6F6B"},
        {"label": "Open Purchase Orders", "value": open_pos, "trend": "", "icon": "shopping_cart", "color": "#E8A33D"},
        {"label": "Low Stock Items", "value": low_count, "trend": "", "icon": "warning", "color": "#C0463C"},
    ]


@router.get("/analytics/activity-heatmap")
def activity_heatmap(db: Session = Depends(get_db)):
    """Returns daily movement counts for last 12 weeks — for heatmap visualization."""
    cutoff = datetime.now(timezone.utc) - timedelta(weeks=12)

    rows = (
        db.query(
            func.date(StockMovement.created_at).label("day"),
            func.count(StockMovement.id).label("count"),
        )
        .filter(StockMovement.created_at >= cutoff)
        .group_by(func.date(StockMovement.created_at))
        .all()
    )

    return [{"date": str(r.day), "count": r.count} for r in rows]