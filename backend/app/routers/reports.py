import csv
import io
import csv as csv_module
import io as io_module

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import UploadFile, File
from app.models.item import Item
from app.core.database import get_db
from app.models.item import Item
from app.models.stock import StockLevel, StockMovement
from app.models.organization import Category

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



@router.post("/reports/import-items")
async def import_items_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Bulk import items from a CSV with columns: sku,name,unit,unit_price,reorder_threshold,description"""
    content = await file.read()
    text = content.decode("utf-8")
    reader = csv_module.DictReader(io_module.StringIO(text))

    created, skipped, errors = 0, 0, []
    for i, row in enumerate(reader, start=2):  # row 1 is header
        try:
            sku = row.get("sku", "").strip()
            name = row.get("name", "").strip()
            if not sku or not name:
                errors.append(f"Row {i}: missing sku or name")
                continue
            existing = db.query(Item).filter(Item.sku == sku).first()
            if existing:
                skipped += 1
                continue
            item = Item(
                sku=sku,
                name=name,
                unit=row.get("unit", "pcs").strip() or "pcs",
                unit_price=float(row.get("unit_price", 0) or 0),
                reorder_threshold=int(row.get("reorder_threshold", 10) or 10),
                description=row.get("description", "").strip() or None,
            )
            db.add(item)
            created += 1
        except Exception as e:
            errors.append(f"Row {i}: {e}")

    db.commit()
    return {"created": created, "skipped_existing": skipped, "errors": errors}


@router.get("/reports/valuation-by-category")
def valuation_by_category(db: Session = Depends(get_db)):
    totals = dict(
        db.query(StockLevel.item_id, func.coalesce(func.sum(StockLevel.quantity), 0))
        .group_by(StockLevel.item_id)
        .all()
    )
    result = {}
    for item in db.query(Item).all():
        cat_name = item.category.name if item.category else "Uncategorized"
        qty = totals.get(item.id, 0)
        value = float(item.unit_price) * qty
        if cat_name not in result:
            result[cat_name] = {"category": cat_name, "total_units": 0, "total_value": 0.0}
        result[cat_name]["total_units"] += qty
        result[cat_name]["total_value"] += value

    return sorted(result.values(), key=lambda x: x["total_value"], reverse=True)

@router.get("/reports/abc-analysis")
def abc_analysis(db: Session = Depends(get_db)):
    """Classifies items into A/B/C based on cumulative value contribution (Pareto)."""
    totals = dict(
        db.query(StockLevel.item_id, func.coalesce(func.sum(StockLevel.quantity), 0))
        .group_by(StockLevel.item_id)
        .all()
    )
    items_value = []
    for item in db.query(Item).all():
        qty = totals.get(item.id, 0)
        value = float(item.unit_price) * qty
        items_value.append({"sku": item.sku, "name": item.name, "value": value})

    items_value.sort(key=lambda x: x["value"], reverse=True)
    total_value = sum(i["value"] for i in items_value) or 1

    cumulative = 0
    for i in items_value:
        cumulative += i["value"]
        pct = cumulative / total_value * 100
        i["cumulative_pct"] = round(pct, 1)
        i["class"] = "A" if pct <= 80 else ("B" if pct <= 95 else "C")

    return items_value



@router.get("/reports/reorder-suggestions")
def reorder_suggestions(db: Session = Depends(get_db)):
    """
    For every low-stock item, suggests a reorder quantity (tops up to 2x threshold)
    and groups suggestions by supplier so you know what to order from whom.
    """
    totals = dict(
        db.query(StockLevel.item_id, func.coalesce(func.sum(StockLevel.quantity), 0))
        .group_by(StockLevel.item_id)
        .all()
    )

    suggestions_by_supplier = {}
    for item in db.query(Item).all():
        qty = totals.get(item.id, 0)
        if qty > item.reorder_threshold:
            continue

        suggested_qty = max((item.reorder_threshold * 2) - qty, 1)
        supplier_name = item.supplier.name if item.supplier else "No Supplier Assigned"
        supplier_id = item.supplier_id

        key = supplier_id if supplier_id else "none"
        if key not in suggestions_by_supplier:
            suggestions_by_supplier[key] = {
                "supplier_id": supplier_id,
                "supplier_name": supplier_name,
                "items": [],
                "estimated_cost": 0.0,
            }

        cost = float(item.unit_price) * suggested_qty
        suggestions_by_supplier[key]["items"].append({
            "item_id": item.id,
            "sku": item.sku,
            "name": item.name,
            "current_quantity": qty,
            "reorder_threshold": item.reorder_threshold,
            "suggested_quantity": suggested_qty,
            "unit_price": float(item.unit_price),
            "estimated_cost": round(cost, 2),
        })
        suggestions_by_supplier[key]["estimated_cost"] += cost

    result = list(suggestions_by_supplier.values())
    for r in result:
        r["estimated_cost"] = round(r["estimated_cost"], 2)
    result.sort(key=lambda x: x["estimated_cost"], reverse=True)
    return result