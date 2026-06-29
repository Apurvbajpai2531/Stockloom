from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta, timezone

from app.core.database import get_db
from app.models.item import Item
from app.models.stock import StockLevel, StockMovement, MovementType
from app.models.organization import Warehouse

router = APIRouter()

LOOKBACK_DAYS = 30


@router.get("/insights")
def generate_insights(db: Session = Depends(get_db)):
    """
    Synthesizes data from stock levels, movement velocity, and warehouse distribution
    into narrative, actionable insight cards — a single feed instead of separate reports.
    """
    insights = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)

    totals = dict(
        db.query(StockLevel.item_id, func.coalesce(func.sum(StockLevel.quantity), 0))
        .group_by(StockLevel.item_id)
        .all()
    )
    outbound_sums = dict(
        db.query(StockMovement.item_id, func.coalesce(func.sum(StockMovement.quantity), 0))
        .filter(StockMovement.movement_type == MovementType.OUTBOUND, StockMovement.created_at >= cutoff)
        .group_by(StockMovement.item_id)
        .all()
    )

    items = db.query(Item).all()

    # Insight 1: Critical stockout risks
    critical_items = []
    for item in items:
        qty = totals.get(item.id, 0)
        velocity = outbound_sums.get(item.id, 0) / LOOKBACK_DAYS
        if velocity > 0:
            days_left = qty / velocity
            if days_left <= 7:
                critical_items.append({"sku": item.sku, "name": item.name, "days": round(days_left, 1)})

    if critical_items:
        worst = sorted(critical_items, key=lambda x: x["days"])[:3]
        insights.append({
            "type": "critical_stockout",
            "icon": "local_fire_department",
            "color": "#C0463C",
            "title": f"{len(critical_items)} item(s) at risk of stocking out within a week",
            "detail": ", ".join(f"{w['sku']} (~{w['days']}d)" for w in worst),
            "action_label": "View Forecasting",
            "action_url": "/forecasting",
        })

    # Insight 2: Dead stock (no movement, high quantity)
    dead_stock = [
        item for item in items
        if outbound_sums.get(item.id, 0) == 0 and totals.get(item.id, 0) > item.reorder_threshold * 3
    ]
    if dead_stock:
        top_dead = sorted(dead_stock, key=lambda i: totals.get(i.id, 0), reverse=True)[:3]
        insights.append({
            "type": "dead_stock",
            "icon": "inventory",
            "color": "#5B6275",
            "title": f"{len(dead_stock)} item(s) appear to be dead stock — overstocked with zero recent sales",
            "detail": ", ".join(f"{i.sku} ({totals.get(i.id, 0)} units idle)" for i in top_dead),
            "action_label": "View Items",
            "action_url": "/items",
        })

    # Insight 3: Warehouse imbalance
    wh_totals = dict(
        db.query(StockLevel.warehouse_id, func.coalesce(func.sum(StockLevel.quantity), 0))
        .group_by(StockLevel.warehouse_id)
        .all()
    )
    if len(wh_totals) >= 2:
        max_wh = max(wh_totals.items(), key=lambda x: x[1])
        min_wh = min(wh_totals.items(), key=lambda x: x[1])
        if max_wh[1] > 0 and min_wh[1] / max(max_wh[1], 1) < 0.3:
            max_name = db.query(Warehouse).get(max_wh[0])
            min_name = db.query(Warehouse).get(min_wh[0])
            insights.append({
                "type": "warehouse_imbalance",
                "icon": "balance",
                "color": "#E8A33D",
                "title": "Significant stock imbalance detected between warehouses",
                "detail": f"{max_name.name if max_name else 'Warehouse'} holds {max_wh[1]} units while {min_name.name if min_name else 'Warehouse'} holds only {min_wh[1]}",
                "action_label": "View Rebalancing",
                "action_url": "/rebalancing",
            })

    # Insight 4: Fast movers worth highlighting
    fast_movers = sorted(
        ((item, outbound_sums.get(item.id, 0)) for item in items),
        key=lambda x: x[1], reverse=True,
    )[:1]
    if fast_movers and fast_movers[0][1] > 0:
        item, qty = fast_movers[0]
        insights.append({
            "type": "top_mover",
            "icon": "trending_up",
            "color": "#2F6F6B",
            "title": f"{item.name} is your fastest-moving item this month",
            "detail": f"{qty} units sold in the last {LOOKBACK_DAYS} days — consider increasing reorder threshold",
            "action_label": "View Item",
            "action_url": f"/items/{item.id}",
        })

    # Insight 5: Healthy baseline (if nothing urgent)
    if not insights:
        insights.append({
            "type": "all_good",
            "icon": "check_circle",
            "color": "#2F6F6B",
            "title": "Everything looks healthy",
            "detail": "No critical stockouts, dead stock, or warehouse imbalances detected right now.",
            "action_label": "View Dashboard",
            "action_url": "/dashboard",
        })

    return insights