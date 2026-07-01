from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.models.item import Item
from app.models.stock import StockLevel, StockMovement, MovementType

router = APIRouter()


@router.get("/anomaly/detect")
def detect_anomalies(db: Session = Depends(get_db)):
    """
    Scans last 30 days of movements for statistical anomalies:
    - Single movement > 3x average daily volume
    - Sudden stock drop > 50% in one day
    - Multiple adjustments on same item (possible data manipulation)
    """
    anomalies = []
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=30)

    for item in db.query(Item).all():
        movements = (
            db.query(StockMovement)
            .filter(StockMovement.item_id == item.id, StockMovement.created_at >= cutoff)
            .order_by(StockMovement.created_at.desc())
            .all()
        )

        if not movements:
            continue

        quantities = [m.quantity for m in movements]
        if len(quantities) < 2:
            continue

        avg_qty = sum(quantities) / len(quantities)
        std_dev = (sum((q - avg_qty) ** 2 for q in quantities) / len(quantities)) ** 0.5

        for m in movements:
            z_score = abs(m.quantity - avg_qty) / (std_dev or 1)

            if z_score > 3:
                anomalies.append({
                    "severity": "high",
                    "icon": "bolt",
                    "color": "#C0463C",
                    "item_id": item.id,
                    "sku": item.sku,
                    "name": item.name,
                    "type": "Statistical Spike",
                    "description": f"Movement of {m.quantity} units is {z_score:.1f}x standard deviation above normal (avg: {avg_qty:.0f})",
                    "date": m.created_at.isoformat() if m.created_at else None,
                })
                break

        adjustments = [m for m in movements if m.movement_type == MovementType.ADJUSTMENT]
        if len(adjustments) >= 3:
            anomalies.append({
                "severity": "medium",
                "icon": "edit_note",
                "color": "#E8A33D",
                "item_id": item.id,
                "sku": item.sku,
                "name": item.name,
                "type": "Frequent Adjustments",
                "description": f"{len(adjustments)} manual adjustments in 30 days — unusual for normal operations",
                "date": adjustments[0].created_at.isoformat() if adjustments[0].created_at else None,
            })

        outbound_movements = [m for m in movements if m.movement_type == MovementType.OUTBOUND]
        if outbound_movements:
            largest = max(outbound_movements, key=lambda x: x.quantity)
            total_stock = (
                db.query(func.coalesce(func.sum(StockLevel.quantity), 0))
                .filter(StockLevel.item_id == item.id)
                .scalar() or 0
            )
            if total_stock > 0 and largest.quantity > total_stock * 0.6:
                anomalies.append({
                    "severity": "medium",
                    "icon": "moving",
                    "color": "#E8A33D",
                    "item_id": item.id,
                    "sku": item.sku,
                    "name": item.name,
                    "type": "Large Single Outbound",
                    "description": f"Single outbound of {largest.quantity} units = {(largest.quantity/total_stock*100):.0f}% of current stock",
                    "date": largest.created_at.isoformat() if largest.created_at else None,
                })

    anomalies.sort(key=lambda x: (0 if x["severity"] == "high" else 1, x["sku"]))
    return {"count": len(anomalies), "anomalies": anomalies[:20]}


@router.get("/anomaly/demand-forecast-calendar")
def demand_forecast_calendar(db: Session = Depends(get_db)):
    """
    Predicts demand for next 30 days per item using 30-day velocity.
    Returns calendar-ready data: {date, predicted_units, items_at_risk}.
    """
    from datetime import date as date_type

    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    outbound_by_item = dict(
        db.query(StockMovement.item_id, func.coalesce(func.sum(StockMovement.quantity), 0))
        .filter(StockMovement.movement_type == MovementType.OUTBOUND, StockMovement.created_at >= cutoff)
        .group_by(StockMovement.item_id)
        .all()
    )
    totals = dict(
        db.query(StockLevel.item_id, func.coalesce(func.sum(StockLevel.quantity), 0))
        .group_by(StockLevel.item_id)
        .all()
    )

    velocities = {}
    for item in db.query(Item).all():
        v = outbound_by_item.get(item.id, 0) / 30
        if v > 0:
            velocities[item] = v

    calendar_data = []
    for day_offset in range(1, 31):
        forecast_date = (datetime.now() + timedelta(days=day_offset)).strftime("%Y-%m-%d")
        total_predicted = 0
        items_at_risk = []
        for item, daily_v in velocities.items():
            predicted = round(daily_v * day_offset)
            current = totals.get(item.id, 0)
            total_predicted += round(daily_v)
            if predicted >= current:
                items_at_risk.append(item.sku)

        calendar_data.append({
            "date": forecast_date,
            "predicted_units": total_predicted,
            "items_at_risk": items_at_risk[:3],
            "risk_count": len(items_at_risk),
        })

    return calendar_data