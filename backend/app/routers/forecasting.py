from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.models.item import Item
from app.models.stock import StockLevel, StockMovement, MovementType

router = APIRouter()

LOOKBACK_DAYS = 30


@router.get("/forecasting/stockout-risk")
def stockout_risk(db: Session = Depends(get_db)):
    """
    Calculates daily outbound velocity per item over the last 30 days,
    then estimates days-until-stockout based on current stock levels.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)

    totals = dict(
        db.query(StockLevel.item_id, func.coalesce(func.sum(StockLevel.quantity), 0))
        .group_by(StockLevel.item_id)
        .all()
    )

    outbound_sums = dict(
        db.query(StockMovement.item_id, func.coalesce(func.sum(StockMovement.quantity), 0))
        .filter(
            StockMovement.movement_type == MovementType.OUTBOUND,
            StockMovement.created_at >= cutoff,
        )
        .group_by(StockMovement.item_id)
        .all()
    )

    results = []
    for item in db.query(Item).all():
        current_qty = totals.get(item.id, 0)
        outbound_total = outbound_sums.get(item.id, 0)
        daily_velocity = outbound_total / LOOKBACK_DAYS

        if daily_velocity <= 0:
            days_until_stockout = None
            risk = "no_movement"
        else:
            days_until_stockout = round(current_qty / daily_velocity, 1)
            if days_until_stockout <= 7:
                risk = "critical"
            elif days_until_stockout <= 21:
                risk = "warning"
            else:
                risk = "healthy"

        results.append({
            "item_id": item.id,
            "sku": item.sku,
            "name": item.name,
            "current_quantity": current_qty,
            "daily_velocity": round(daily_velocity, 2),
            "days_until_stockout": days_until_stockout,
            "risk": risk,
        })

    # Sort: critical first, then by soonest stockout
    risk_order = {"critical": 0, "warning": 1, "healthy": 2, "no_movement": 3}
    results.sort(key=lambda r: (risk_order[r["risk"]], r["days_until_stockout"] or 9999))
    return results


@router.get("/forecasting/stockout-risk/{item_id}")
def stockout_risk_for_item(item_id: int, db: Session = Depends(get_db)):
    """Same calc as above, but for a single item — used on the item detail page."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)

    item = db.query(Item).get(item_id)
    if not item:
        return {"error": "Item not found"}

    current_qty = (
        db.query(func.coalesce(func.sum(StockLevel.quantity), 0))
        .filter(StockLevel.item_id == item_id)
        .scalar()
        or 0
    )
    outbound_total = (
        db.query(func.coalesce(func.sum(StockMovement.quantity), 0))
        .filter(
            StockMovement.item_id == item_id,
            StockMovement.movement_type == MovementType.OUTBOUND,
            StockMovement.created_at >= cutoff,
        )
        .scalar()
        or 0
    )
    daily_velocity = outbound_total / LOOKBACK_DAYS

    if daily_velocity <= 0:
        return {"daily_velocity": 0, "days_until_stockout": None, "risk": "no_movement", "current_quantity": current_qty}

    days_until_stockout = round(current_qty / daily_velocity, 1)
    risk = "critical" if days_until_stockout <= 7 else ("warning" if days_until_stockout <= 21 else "healthy")

    return {
        "daily_velocity": round(daily_velocity, 2),
        "days_until_stockout": days_until_stockout,
        "risk": risk,
        "current_quantity": current_qty,
    }


@router.get("/forecasting/rebalance-suggestions")
def rebalance_suggestions(db: Session = Depends(get_db)):
    """
    Finds items where one warehouse is overstocked and another is understocked
    relative to the item's reorder threshold, and suggests a transfer.
    """
    from app.models.organization import Warehouse

    suggestions = []
    for item in db.query(Item).all():
        levels = db.query(StockLevel).filter(StockLevel.item_id == item.id).all()
        if len(levels) < 2:
            continue

        surplus = [l for l in levels if l.quantity > item.reorder_threshold * 1.5]
        deficit = [l for l in levels if l.quantity <= item.reorder_threshold]

        if not surplus or not deficit:
            continue

        surplus.sort(key=lambda l: l.quantity, reverse=True)
        deficit.sort(key=lambda l: l.quantity)

        source = surplus[0]
        target = deficit[0]
        transferable = min(
            source.quantity - item.reorder_threshold,
            item.reorder_threshold - target.quantity,
        )
        if transferable <= 0:
            continue

        source_wh = db.query(Warehouse).get(source.warehouse_id)
        target_wh = db.query(Warehouse).get(target.warehouse_id)

        suggestions.append({
            "item_id": item.id,
            "sku": item.sku,
            "name": item.name,
            "from_warehouse_id": source.warehouse_id,
            "from_warehouse_name": source_wh.name if source_wh else "Unknown",
            "from_quantity": source.quantity,
            "to_warehouse_id": target.warehouse_id,
            "to_warehouse_name": target_wh.name if target_wh else "Unknown",
            "to_quantity": target.quantity,
            "suggested_transfer_qty": transferable,
        })

    return suggestions