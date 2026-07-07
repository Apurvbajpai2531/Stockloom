from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.reservation import StockReservation
from app.models.stock import StockLevel

router = APIRouter()


class ReservationCreate(BaseModel):
    item_id: int
    warehouse_id: int
    quantity: int
    reference: str
    reason: Optional[str] = None


@router.get("/reservations")
def list_reservations(status: str = "active", db: Session = Depends(get_db)):
    rows = (
        db.query(StockReservation)
        .filter(StockReservation.status == status)
        .order_by(StockReservation.created_at.desc())
        .all()
    )

    result = []
    for r in rows:
        result.append(
            {
                "id": r.id,
                "item_id": r.item_id,
                "sku": r.item.sku if r.item else None,
                "item_name": r.item.name if r.item else None,
                "warehouse_id": r.warehouse_id,
                "warehouse_name": r.warehouse.name if r.warehouse else None,
                "quantity": r.quantity,
                "reference": r.reference,
                "reason": r.reason,
                "status": r.status,
                "created_by": r.created_by,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
        )
    return result


@router.post("/reservations", status_code=201)
def create_reservation(
    payload: ReservationCreate,
    db: Session = Depends(get_db),
    user: str = Depends(get_current_user),
):
    # Check available stock (total - already reserved)
    total_qty = (
        db.query(func.coalesce(func.sum(StockLevel.quantity), 0))
        .filter(
            StockLevel.item_id == payload.item_id,
            StockLevel.warehouse_id == payload.warehouse_id,
        )
        .scalar()
        or 0
    )
    already_reserved = (
        db.query(func.coalesce(func.sum(StockReservation.quantity), 0))
        .filter(
            StockReservation.item_id == payload.item_id,
            StockReservation.warehouse_id == payload.warehouse_id,
            StockReservation.status == "active",
        )
        .scalar()
        or 0
    )
    available = total_qty - already_reserved
    if payload.quantity > available:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient available stock. Total: {total_qty}, Reserved: {already_reserved}, Available: {available}",
        )

    res = StockReservation(
        item_id=payload.item_id,
        warehouse_id=payload.warehouse_id,
        quantity=payload.quantity,
        reference=payload.reference,
        reason=payload.reason,
        created_by=user,
    )
    db.add(res)
    db.commit()
    db.refresh(res)
    return {
        "id": res.id,
        "reference": res.reference,
        "available_after": available - payload.quantity,
    }


@router.post("/reservations/{res_id}/fulfil", status_code=200)
def fulfil_reservation(res_id: int, db: Session = Depends(get_db)):
    res = db.query(StockReservation).get(res_id)
    if not res:
        raise HTTPException(status_code=404, detail="Reservation not found")
    if res.status != "active":
        raise HTTPException(
            status_code=400, detail="Only active reservations can be fulfilled"
        )

    from app.models.stock import StockLevel, StockMovement, MovementType

    level = (
        db.query(StockLevel)
        .filter(
            StockLevel.item_id == res.item_id,
            StockLevel.warehouse_id == res.warehouse_id,
        )
        .first()
    )
    if not level or level.quantity < res.quantity:
        raise HTTPException(
            status_code=400, detail="Insufficient physical stock to fulfil"
        )

    level.quantity -= res.quantity
    db.add(
        StockMovement(
            item_id=res.item_id,
            warehouse_id=res.warehouse_id,
            movement_type=MovementType.OUTBOUND,
            quantity=res.quantity,
            reference=res.reference,
            notes=f"Fulfilled reservation #{res_id}",
        )
    )
    res.status = "fulfilled"
    db.commit()
    return {"status": "fulfilled", "reference": res.reference}


@router.post("/reservations/{res_id}/cancel", status_code=200)
def cancel_reservation(res_id: int, db: Session = Depends(get_db)):
    res = db.query(StockReservation).get(res_id)
    if not res:
        raise HTTPException(status_code=404, detail="Reservation not found")
    if res.status != "active":
        raise HTTPException(
            status_code=400, detail="Only active reservations can be cancelled"
        )
    res.status = "cancelled"
    db.commit()
    return {"status": "cancelled"}


@router.get("/reservations/availability/{item_id}/{warehouse_id}")
def check_availability(item_id: int, warehouse_id: int, db: Session = Depends(get_db)):
    total = (
        db.query(func.coalesce(func.sum(StockLevel.quantity), 0))
        .filter(StockLevel.item_id == item_id, StockLevel.warehouse_id == warehouse_id)
        .scalar()
        or 0
    )
    reserved = (
        db.query(func.coalesce(func.sum(StockReservation.quantity), 0))
        .filter(
            StockReservation.item_id == item_id,
            StockReservation.warehouse_id == warehouse_id,
            StockReservation.status == "active",
        )
        .scalar()
        or 0
    )
    return {
        "item_id": item_id,
        "warehouse_id": warehouse_id,
        "total_quantity": int(total),
        "reserved_quantity": int(reserved),
        "available_quantity": int(total - reserved),
    }
