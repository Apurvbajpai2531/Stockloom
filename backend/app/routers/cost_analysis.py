import math
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.item import Item
from app.models.stock import MovementType, StockLevel, StockMovement

router = APIRouter()

HOLDING_COST_RATE = 0.25  # 25% of unit price per year (industry standard)
ORDERING_COST = 50.0  # Fixed cost per order placed ($50 default)


@router.get("/cost-analysis/eoq")
def eoq_analysis(db: Session = Depends(get_db)):
    """
    Economic Order Quantity (EOQ) per item.
    EOQ = sqrt(2 * Annual Demand * Ordering Cost / Holding Cost per unit)
    Industry formula used by SAP, Oracle WMS.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=365)
    outbound_by_item = dict(
        db.query(
            StockMovement.item_id, func.coalesce(func.sum(StockMovement.quantity), 0)
        )
        .filter(
            StockMovement.movement_type == MovementType.OUTBOUND,
            StockMovement.created_at >= cutoff,
        )
        .group_by(StockMovement.item_id)
        .all()
    )

    results = []
    for item in db.query(Item).all():
        annual_demand = outbound_by_item.get(item.id, 0)
        if annual_demand == 0:
            continue

        unit_price = float(item.unit_price)
        holding_cost = unit_price * HOLDING_COST_RATE
        if holding_cost <= 0:
            continue

        eoq = math.sqrt((2 * annual_demand * ORDERING_COST) / holding_cost)
        orders_per_year = annual_demand / eoq
        avg_cycle_stock = eoq / 2
        total_annual_cost = (orders_per_year * ORDERING_COST) + (
            avg_cycle_stock * holding_cost
        )

        results.append(
            {
                "item_id": item.id,
                "sku": item.sku,
                "name": item.name,
                "unit_price": unit_price,
                "annual_demand": int(annual_demand),
                "eoq": round(eoq),
                "orders_per_year": round(orders_per_year, 1),
                "avg_cycle_stock": round(avg_cycle_stock),
                "total_annual_cost": round(total_annual_cost, 2),
                "current_threshold": item.reorder_threshold,
                "suggested_threshold": round(eoq * 0.25),
            }
        )

    results.sort(key=lambda x: x["total_annual_cost"], reverse=True)
    return results


@router.get("/cost-analysis/holding-cost")
def holding_cost_summary(db: Session = Depends(get_db)):
    """Total holding cost of current inventory."""
    totals = dict(
        db.query(StockLevel.item_id, func.coalesce(func.sum(StockLevel.quantity), 0))
        .group_by(StockLevel.item_id)
        .all()
    )

    total_holding = 0
    category_costs = {}
    for item in db.query(Item).all():
        qty = totals.get(item.id, 0)
        holding = float(item.unit_price) * qty * HOLDING_COST_RATE
        total_holding += holding

        cat_name = item.category.name if item.category else "Uncategorized"
        category_costs[cat_name] = category_costs.get(cat_name, 0) + holding

    return {
        "total_annual_holding_cost": round(total_holding, 2),
        "monthly_holding_cost": round(total_holding / 12, 2),
        "holding_rate_used": f"{HOLDING_COST_RATE*100:.0f}%",
        "by_category": [
            {"category": k, "annual_holding_cost": round(v, 2)}
            for k, v in sorted(category_costs.items(), key=lambda x: x[1], reverse=True)
        ],
    }
