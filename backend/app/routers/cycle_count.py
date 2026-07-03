from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.cycle_count import CycleCount, CycleCountLine
from app.models.stock import StockLevel
from app.models.item import Item

router = APIRouter()


@router.get("/cycle-counts")
def list_cycle_counts(db: Session = Depends(get_db)):
    counts = db.query(CycleCount).order_by(CycleCount.created_at.desc()).all()
    return [
        {
            "id": c.id,
            "warehouse_id": c.warehouse_id,
            "warehouse_name": c.warehouse.name if c.warehouse else None,
            "status": c.status,
            "created_by": c.created_by,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "line_count": len(c.lines),
            "verified_count": sum(1 for l in c.lines if l.is_verified),
            "variance_count": sum(1 for l in c.lines if l.variance and l.variance != 0),
        }
        for c in counts
    ]


@router.post("/cycle-counts", status_code=201)
def create_cycle_count(warehouse_id: int, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    """Creates a cycle count session for a warehouse — snapshots current system quantities."""
    cc = CycleCount(warehouse_id=warehouse_id, created_by=user)
    db.add(cc)
    db.flush()

    levels = db.query(StockLevel).filter(StockLevel.warehouse_id == warehouse_id).all()
    for lvl in levels:
        db.add(CycleCountLine(
            cycle_count_id=cc.id,
            item_id=lvl.item_id,
            system_quantity=lvl.quantity,
        ))

    db.commit()
    db.refresh(cc)
    return {"id": cc.id, "line_count": len(levels)}


@router.get("/cycle-counts/{cc_id}")
def get_cycle_count(cc_id: int, db: Session = Depends(get_db)):
    cc = db.query(CycleCount).get(cc_id)
    if not cc:
        raise HTTPException(status_code=404, detail="Cycle count not found")
    return {
        "id": cc.id,
        "warehouse_id": cc.warehouse_id,
        "warehouse_name": cc.warehouse.name if cc.warehouse else None,
        "status": cc.status,
        "created_by": cc.created_by,
        "created_at": cc.created_at.isoformat() if cc.created_at else None,
        "lines": [
            {
                "id": l.id,
                "item_id": l.item_id,
                "sku": l.item.sku if l.item else None,
                "name": l.item.name if l.item else None,
                "system_quantity": l.system_quantity,
                "counted_quantity": l.counted_quantity,
                "variance": l.variance,
                "is_verified": l.is_verified,
            }
            for l in cc.lines
        ],
    }


class CountSubmit(BaseModel):
    line_id: int
    counted_quantity: int


@router.post("/cycle-counts/{cc_id}/submit-count")
def submit_count(cc_id: int, payload: CountSubmit, db: Session = Depends(get_db)):
    cc = db.query(CycleCount).get(cc_id)
    if not cc or cc.status != "open":
        raise HTTPException(status_code=400, detail="Cycle count not found or already completed")

    line = db.query(CycleCountLine).filter(
        CycleCountLine.id == payload.line_id,
        CycleCountLine.cycle_count_id == cc_id,
    ).first()
    if not line:
        raise HTTPException(status_code=404, detail="Line not found")

    line.counted_quantity = payload.counted_quantity
    line.variance = payload.counted_quantity - line.system_quantity
    line.is_verified = True
    db.commit()
    return {"variance": line.variance, "system": line.system_quantity, "counted": line.counted_quantity}


@router.post("/cycle-counts/{cc_id}/complete")
def complete_cycle_count(cc_id: int, apply_adjustments: bool = False, db: Session = Depends(get_db)):
    """Completes the cycle count. Optionally applies adjustments to correct system quantities."""
    cc = db.query(CycleCount).get(cc_id)
    if not cc or cc.status != "open":
        raise HTTPException(status_code=400, detail="Cycle count not found or already completed")

    if apply_adjustments:
        from app.models.stock import StockLevel, StockMovement, MovementType
        for line in cc.lines:
            if line.counted_quantity is not None and line.variance != 0:
                lvl = db.query(StockLevel).filter(
                    StockLevel.item_id == line.item_id,
                    StockLevel.warehouse_id == cc.warehouse_id,
                ).first()
                if lvl:
                    lvl.quantity = line.counted_quantity
                    db.add(StockMovement(
                        item_id=line.item_id,
                        warehouse_id=cc.warehouse_id,
                        movement_type=MovementType.ADJUSTMENT,
                        quantity=line.counted_quantity,
                        reference=f"CC-{cc_id}",
                        notes=f"Cycle count adjustment (variance: {line.variance})",
                    ))

    cc.status = "completed"
    cc.completed_at = datetime.now(timezone.utc)
    db.commit()
    return {"status": "completed", "adjustments_applied": apply_adjustments}