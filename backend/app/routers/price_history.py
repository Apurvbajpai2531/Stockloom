from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.price_history import PriceHistory
from app.models.item import Item

router = APIRouter()


@router.get("/price-history/{item_id}")
def get_price_history(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    history = (
        db.query(PriceHistory)
        .filter(PriceHistory.item_id == item_id)
        .order_by(PriceHistory.changed_at.asc())
        .all()
    )
    return {
        "item_id": item_id,
        "sku": item.sku,
        "current_price": float(item.unit_price),
        "history": [
            {
                "old_price": float(h.old_price),
                "new_price": float(h.new_price),
                "changed_by": h.changed_by,
                "changed_at": h.changed_at.isoformat() if h.changed_at else None,
            }
            for h in history
        ],
    }