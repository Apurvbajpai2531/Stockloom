from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.notification import Notification
from app.models.item import Item
from app.models.stock import StockLevel
from sqlalchemy import func

router = APIRouter()


@router.get("/notifications")
def list_notifications(unread_only: bool = False, db: Session = Depends(get_db)):
    q = db.query(Notification)
    if unread_only:
        q = q.filter(Notification.is_read == False)
    notifs = q.order_by(Notification.created_at.desc()).limit(50).all()
    return [
        {
            "id": n.id, "title": n.title, "message": n.message,
            "severity": n.severity, "is_read": n.is_read,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        }
        for n in notifs
    ]


@router.post("/notifications/{notif_id}/mark-read")
def mark_read(notif_id: int, db: Session = Depends(get_db)):
    n = db.query(Notification).get(notif_id)
    if n:
        n.is_read = True
        db.commit()
    return {"ok": True}


@router.post("/notifications/generate-low-stock")
def generate_low_stock_notifications(db: Session = Depends(get_db)):
    """Scans for low-stock items and creates notifications (call periodically, e.g. via a cron or button)."""
    totals = dict(
        db.query(StockLevel.item_id, func.coalesce(func.sum(StockLevel.quantity), 0))
        .group_by(StockLevel.item_id)
        .all()
    )
    created = 0
    for item in db.query(Item).all():
        qty = totals.get(item.id, 0)
        if qty <= item.reorder_threshold:
            existing = (
                db.query(Notification)
                .filter(Notification.title == f"Low stock: {item.sku}", Notification.is_read == False)
                .first()
            )
            if existing:
                continue
            severity = "critical" if qty == 0 else "warning"
            db.add(Notification(
                title=f"Low stock: {item.sku}",
                message=f"{item.name} has only {qty} units left (threshold: {item.reorder_threshold})",
                severity=severity,
            ))
            created += 1
    db.commit()
    return {"created": created}
