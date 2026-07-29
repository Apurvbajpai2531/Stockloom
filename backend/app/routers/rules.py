from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.alert_rule import AlertRule
from app.models.item import Item
from app.models.stock import StockLevel

router = APIRouter()


class RuleCreate(BaseModel):
    name: str
    item_id: Optional[int] = None
    warehouse_id: Optional[int] = None
    condition: str  # below, above, equals
    threshold: int


@router.get("/rules")
def list_rules(db: Session = Depends(get_db)):
    rules = db.query(AlertRule).order_by(AlertRule.created_at.desc()).all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "item_id": r.item_id,
            "warehouse_id": r.warehouse_id,
            "condition": r.condition,
            "threshold": r.threshold,
            "is_active": r.is_active,
            "created_by": r.created_by,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rules
    ]


@router.post("/rules", status_code=201)
def create_rule(
    payload: RuleCreate,
    db: Session = Depends(get_db),
    user: str = Depends(get_current_user),
):
    if payload.condition not in ("below", "above", "equals"):
        raise HTTPException(
            status_code=400, detail="condition must be 'below', 'above', or 'equals'"
        )

    rule = AlertRule(
        name=payload.name,
        item_id=payload.item_id,
        warehouse_id=payload.warehouse_id,
        condition=payload.condition,
        threshold=payload.threshold,
        created_by=user,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return {"id": rule.id, "name": rule.name}


@router.delete("/rules/{rule_id}", status_code=204)
def delete_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = db.query(AlertRule).get(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    db.delete(rule)
    db.commit()


@router.get("/rules/evaluate")
def evaluate_rules(db: Session = Depends(get_db)):
    """
    Evaluates all active rules against current stock levels.
    Returns list of triggered rules with context.
    """
    rules = db.query(AlertRule).filter(AlertRule.is_active).all()
    triggered = []

    for rule in rules:
        items_to_check = (
            db.query(Item).filter(Item.id == rule.item_id).all()
            if rule.item_id
            else db.query(Item).all()
        )

        for item in items_to_check:
            qty_query = db.query(
                func.coalesce(func.sum(StockLevel.quantity), 0)
            ).filter(StockLevel.item_id == item.id)
            if rule.warehouse_id:
                qty_query = qty_query.filter(
                    StockLevel.warehouse_id == rule.warehouse_id
                )
            qty = qty_query.scalar() or 0

            fired = False
            if rule.condition == "below" and qty < rule.threshold:
                fired = True
            elif rule.condition == "above" and qty > rule.threshold:
                fired = True
            elif rule.condition == "equals" and qty == rule.threshold:
                fired = True

            if fired:
                triggered.append(
                    {
                        "rule_id": rule.id,
                        "rule_name": rule.name,
                        "item_id": item.id,
                        "sku": item.sku,
                        "name": item.name,
                        "current_quantity": qty,
                        "condition": rule.condition,
                        "threshold": rule.threshold,
                        "warehouse_id": rule.warehouse_id,
                    }
                )

    return {"triggered_count": len(triggered), "triggered": triggered}
