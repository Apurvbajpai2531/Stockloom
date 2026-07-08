import io
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

from app.core.database import get_db
from app.models.purchase_order import PurchaseOrder, PurchaseOrderLine, POStatus
from app.models.stock import StockLevel, StockMovement, MovementType
from app.schemas.purchase_order import PurchaseOrderCreate, PurchaseOrderOut

router = APIRouter()


@router.get("/purchase-orders", response_model=list[PurchaseOrderOut])
def list_purchase_orders(status: str | None = None, db: Session = Depends(get_db)):
    q = db.query(PurchaseOrder)
    if status:
        q = q.filter(PurchaseOrder.status == status)
    return q.order_by(PurchaseOrder.created_at.desc()).all()


@router.get("/purchase-orders/{po_id}", response_model=PurchaseOrderOut)
def get_purchase_order(po_id: int, db: Session = Depends(get_db)):
    po = db.query(PurchaseOrder).get(po_id)
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return po


@router.post("/purchase-orders", response_model=PurchaseOrderOut, status_code=201)
def create_purchase_order(payload: PurchaseOrderCreate, db: Session = Depends(get_db)):
    if not payload.lines:
        raise HTTPException(
            status_code=400, detail="Purchase order needs at least one line item"
        )

    po = PurchaseOrder(
        po_number=payload.po_number,
        supplier_id=payload.supplier_id,
        warehouse_id=payload.warehouse_id,
        notes=payload.notes,
        status=POStatus.DRAFT,
    )
    db.add(po)
    db.flush()

    for line in payload.lines:
        db.add(
            PurchaseOrderLine(
                purchase_order_id=po.id,
                item_id=line.item_id,
                quantity_ordered=line.quantity_ordered,
                unit_cost=line.unit_cost,
            )
        )

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="PO number already exists")
    db.refresh(po)
    return po


@router.post("/purchase-orders/{po_id}/mark-ordered", response_model=PurchaseOrderOut)
def mark_ordered(po_id: int, db: Session = Depends(get_db)):
    po = db.query(PurchaseOrder).get(po_id)
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    if po.status != POStatus.DRAFT:
        raise HTTPException(
            status_code=400, detail="Only draft POs can be marked as ordered"
        )
    po.status = POStatus.ORDERED
    db.commit()
    db.refresh(po)
    return po


@router.post("/purchase-orders/{po_id}/receive", response_model=PurchaseOrderOut)
def receive_purchase_order(po_id: int, db: Session = Depends(get_db)):
    """Receiving a PO adds stock for every line item and logs inbound movements."""
    po = db.query(PurchaseOrder).get(po_id)
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    if po.status not in (POStatus.ORDERED, POStatus.DRAFT):
        raise HTTPException(
            status_code=400, detail="Purchase order already received or cancelled"
        )

    for line in po.lines:
        level = (
            db.query(StockLevel)
            .filter(
                StockLevel.item_id == line.item_id,
                StockLevel.warehouse_id == po.warehouse_id,
            )
            .first()
        )
        if not level:
            level = StockLevel(
                item_id=line.item_id, warehouse_id=po.warehouse_id, quantity=0
            )
            db.add(level)
            db.flush()
        level.quantity += line.quantity_ordered

        db.add(
            StockMovement(
                item_id=line.item_id,
                warehouse_id=po.warehouse_id,
                movement_type=MovementType.INBOUND,
                quantity=line.quantity_ordered,
                reference=po.po_number,
                notes=f"Received from PO {po.po_number}",
            )
        )

    po.status = POStatus.RECEIVED
    po.received_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(po)
    return po


@router.post("/purchase-orders/{po_id}/cancel", response_model=PurchaseOrderOut)
def cancel_purchase_order(po_id: int, db: Session = Depends(get_db)):
    po = db.query(PurchaseOrder).get(po_id)
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    if po.status == POStatus.RECEIVED:
        raise HTTPException(
            status_code=400, detail="Cannot cancel a received purchase order"
        )
    po.status = POStatus.CANCELLED
    db.commit()
    db.refresh(po)
    return po


@router.get("/purchase-orders/{po_id}/pdf")
def export_po_pdf(po_id: int, db: Session = Depends(get_db)):
    po = db.query(PurchaseOrder).get(po_id)
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(f"Purchase Order: {po.po_number}", styles["Title"]))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Status: {po.status.value.upper()}", styles["Normal"]))
    elements.append(
        Paragraph(
            f"Supplier: {po.supplier.name if po.supplier else 'N/A'}", styles["Normal"]
        )
    )
    elements.append(
        Paragraph(
            f"Warehouse: {po.warehouse.name if po.warehouse else 'N/A'}",
            styles["Normal"],
        )
    )
    elements.append(
        Paragraph(
            f"Created: {po.created_at.strftime('%Y-%m-%d %H:%M') if po.created_at else 'N/A'}",
            styles["Normal"],
        )
    )
    elements.append(Spacer(1, 20))

    data = [["SKU", "Item", "Qty Ordered", "Unit Cost", "Line Total"]]
    total = 0
    for line in po.lines:
        line_total = float(line.unit_cost) * line.quantity_ordered
        total += line_total
        data.append(
            [
                line.item.sku,
                line.item.name,
                str(line.quantity_ordered),
                f"${float(line.unit_cost):.2f}",
                f"${line_total:.2f}",
            ]
        )
    data.append(["", "", "", "Total:", f"${total:.2f}"])

    table = Table(data, colWidths=[1 * inch, 2.2 * inch, 1 * inch, 1 * inch, 1 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1C2230")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -2), 0.5, colors.grey),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("LINEABOVE", (0, -1), (-1, -1), 1, colors.black),
            ]
        )
    )
    elements.append(table)

    if po.notes:
        elements.append(Spacer(1, 20))
        elements.append(Paragraph(f"Notes: {po.notes}", styles["Normal"]))

    doc.build(elements)
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=PO_{po.po_number}.pdf"},
    )
