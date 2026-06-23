import csv
import io

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.models.item import Item
from app.models.stock import StockLevel, StockMovement

router = APIRouter()


def _csv_response(rows: list[dict], filename: str) -> StreamingResponse:
    buffer = io.StringIO()
    if rows:
        writer = csv.DictWriter(buffer, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/reports/items.csv")
def export_items_csv(db: Session = Depends(get_db)):
    totals = dict(
        db.query(StockLevel.item_id, func.coalesce(func.sum(StockLevel.quantity), 0))
        .group_by(StockLevel.item_id)
        .all()
    )
    rows = []
    for item in db.query(Item).all():
        rows.append({
            "sku": item.sku,
            "name": item.name,
            "unit": item.unit,
            "unit_price": float(item.unit_price),
            "total_quantity": totals.get(item.id, 0),
            "reorder_threshold": item.reorder_threshold,
        })
    return _csv_response(rows, "items_report.csv")


@router.get("/reports/movements.csv")
def export_movements_csv(db: Session = Depends(get_db)):
    rows = []
    for m in db.query(StockMovement).order_by(StockMovement.created_at.desc()).all():
        rows.append({
            "created_at": m.created_at.isoformat() if m.created_at else "",
            "item_id": m.item_id,
            "warehouse_id": m.warehouse_id,
            "destination_warehouse_id": m.destination_warehouse_id or "",
            "movement_type": m.movement_type.value,
            "quantity": m.quantity,
            "reference": m.reference or "",
        })
    return _csv_response(rows, "movements_report.csv")