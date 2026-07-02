from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.models.item import Item
from app.models.stock import StockLevel, StockMovement, MovementType
from app.models.organization import Supplier
from app.models.purchase_order import PurchaseOrder, POStatus

router = APIRouter()


@router.get("/supplier-analytics/performance")
def supplier_performance(db: Session = Depends(get_db)):
    """
    Per-supplier scorecard:
    - Items supplied
    - Total inventory value held
    - Open PO count
    - Received PO count
    - Average PO fulfillment (draft→received)
    """
    suppliers = db.query(Supplier).all()
    results = []

    totals = dict(
        db.query(StockLevel.item_id, func.coalesce(func.sum(StockLevel.quantity), 0))
        .group_by(StockLevel.item_id)
        .all()
    )

    for sup in suppliers:
        items = db.query(Item).filter(Item.supplier_id == sup.id).all()
        item_count = len(items)

        inv_value = sum(
            float(i.unit_price) * totals.get(i.id, 0) for i in items
        )

        open_pos = (
            db.query(func.count(PurchaseOrder.id))
            .filter(
                PurchaseOrder.supplier_id == sup.id,
                PurchaseOrder.status.in_([POStatus.DRAFT, POStatus.ORDERED]),
            )
            .scalar() or 0
        )
        received_pos = (
            db.query(func.count(PurchaseOrder.id))
            .filter(
                PurchaseOrder.supplier_id == sup.id,
                PurchaseOrder.status == POStatus.RECEIVED,
            )
            .scalar() or 0
        )

        # Avg fulfillment days (created_at → received_at)
        fulfilled = (
            db.query(PurchaseOrder)
            .filter(
                PurchaseOrder.supplier_id == sup.id,
                PurchaseOrder.status == POStatus.RECEIVED,
                PurchaseOrder.received_at.isnot(None),
            )
            .all()
        )
        avg_days = None
        if fulfilled:
            deltas = [
                (po.received_at - po.created_at).total_seconds() / 86400
                for po in fulfilled
                if po.received_at and po.created_at
            ]
            avg_days = round(sum(deltas) / len(deltas), 1) if deltas else None

        # Reliability score (0-100)
        total_pos = open_pos + received_pos
        score = round((received_pos / total_pos) * 100) if total_pos > 0 else None

        results.append({
            "supplier_id": sup.id,
            "supplier_name": sup.name,
            "contact_email": sup.contact_email,
            "item_count": item_count,
            "inventory_value": round(inv_value, 2),
            "open_purchase_orders": open_pos,
            "received_purchase_orders": received_pos,
            "avg_fulfillment_days": avg_days,
            "reliability_score": score,
        })

    results.sort(key=lambda x: x["inventory_value"], reverse=True)
    return results


@router.get("/supplier-analytics/turnover")
def inventory_turnover(db: Session = Depends(get_db)):
    """
    Inventory Turnover Ratio per category: COGS / Avg Inventory Value.
    Also calculates GMROI (Gross Margin Return on Inventory Investment).
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=365)
    from app.models.organization import Category

    totals = dict(
        db.query(StockLevel.item_id, func.coalesce(func.sum(StockLevel.quantity), 0))
        .group_by(StockLevel.item_id)
        .all()
    )
    outbound_by_item = dict(
        db.query(StockMovement.item_id, func.coalesce(func.sum(StockMovement.quantity), 0))
        .filter(
            StockMovement.movement_type == MovementType.OUTBOUND,
            StockMovement.created_at >= cutoff,
        )
        .group_by(StockMovement.item_id)
        .all()
    )

    categories = db.query(Category).all()
    results = []

    for cat in categories:
        items = db.query(Item).filter(Item.category_id == cat.id).all()
        if not items:
            continue

        cogs = sum(
            float(i.unit_price) * outbound_by_item.get(i.id, 0) for i in items
        )
        avg_inv_value = sum(
            float(i.unit_price) * totals.get(i.id, 0) for i in items
        )

        turnover = round(cogs / avg_inv_value, 2) if avg_inv_value > 0 else 0
        # GMROI assumes 40% gross margin (typical for distribution)
        gross_margin = cogs * 0.4
        gmroi = round(gross_margin / avg_inv_value, 2) if avg_inv_value > 0 else 0

        results.append({
            "category": cat.name,
            "item_count": len(items),
            "cogs_annual": round(cogs, 2),
            "avg_inventory_value": round(avg_inv_value, 2),
            "turnover_ratio": turnover,
            "gmroi": gmroi,
            "health": "excellent" if turnover >= 6 else ("good" if turnover >= 3 else ("slow" if turnover >= 1 else "dead")),
        })

    results.sort(key=lambda x: x["turnover_ratio"], reverse=True)
    return results


@router.get("/supplier-analytics/dead-stock")
def dead_stock_report(db: Session = Depends(get_db)):
    """Items with zero outbound movement in 60 days but quantity > reorder threshold."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=60)

    active_item_ids = set(
        row[0] for row in
        db.query(StockMovement.item_id)
        .filter(
            StockMovement.movement_type == MovementType.OUTBOUND,
            StockMovement.created_at >= cutoff,
        )
        .distinct()
        .all()
    )

    totals = dict(
        db.query(StockLevel.item_id, func.coalesce(func.sum(StockLevel.quantity), 0))
        .group_by(StockLevel.item_id)
        .all()
    )

    dead = []
    for item in db.query(Item).all():
        if item.id in active_item_ids:
            continue
        qty = totals.get(item.id, 0)
        if qty <= 0:
            continue
        tied_capital = float(item.unit_price) * qty
        dead.append({
            "item_id": item.id,
            "sku": item.sku,
            "name": item.name,
            "quantity": qty,
            "unit_price": float(item.unit_price),
            "tied_capital": round(tied_capital, 2),
            "days_idle": 60,
        })

    dead.sort(key=lambda x: x["tied_capital"], reverse=True)
    return {"count": len(dead), "total_tied_capital": round(sum(d["tied_capital"] for d in dead), 2), "items": dead}