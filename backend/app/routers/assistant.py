import re

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.models.item import Item
from app.models.stock import StockLevel
from app.models.organization import Warehouse

router = APIRouter()


@router.post("/assistant/query")
def assistant_query(payload: dict, db: Session = Depends(get_db)):
    """
    A free, rule-based assistant that parses natural-language-style questions
    and answers them using real database queries. No external API required.
    """
    text = (payload.get("query") or "").lower().strip()

    if not text:
        return {
            "answer": "Ask me something like 'low stock items' or 'where is SKU-052'."
        }

    totals = dict(
        db.query(StockLevel.item_id, func.coalesce(func.sum(StockLevel.quantity), 0))
        .group_by(StockLevel.item_id)
        .all()
    )

    # Intent: low stock / reorder
    if any(
        kw in text for kw in ["low stock", "reorder", "running out", "need to order"]
    ):
        low_items = []
        for item in db.query(Item).all():
            qty = totals.get(item.id, 0)
            if qty <= item.reorder_threshold:
                low_items.append(f"{item.sku} ({item.name}) — {qty} left")
        if not low_items:
            return {
                "answer": "Nothing is low on stock right now. All items are above their reorder threshold."
            }
        return {
            "answer": f"Found {len(low_items)} item(s) low on stock:",
            "list": low_items[:10],
        }

    # Intent: find a specific SKU
    sku_match = re.search(r"sku[-\s]?(\w+)", text)
    if sku_match or "where is" in text or "find" in text:
        search_term = (
            sku_match.group(0).replace(" ", "-").upper()
            if sku_match
            else text.replace("where is", "").replace("find", "").strip()
        )
        item = (
            db.query(Item)
            .filter(
                (Item.sku.ilike(f"%{search_term}%"))
                | (Item.name.ilike(f"%{search_term}%"))
            )
            .first()
        )
        if not item:
            return {"answer": f"I couldn't find an item matching '{search_term}'."}
        levels = db.query(StockLevel).filter(StockLevel.item_id == item.id).all()
        if not levels:
            return {
                "answer": f"{item.sku} ({item.name}) has no recorded stock in any warehouse."
            }
        breakdown = []
        for log in levels:
            wh = db.query(Warehouse).get(log.warehouse_id)
            breakdown.append(
                f"{wh.name if wh else 'Unknown warehouse'}: {log.quantity} units"
            )
        total_qty = totals.get(item.id, 0)
        return {
            "answer": f"{item.sku} — {item.name} has {total_qty} units total, across:",
            "list": breakdown,
        }

    # Intent: total inventory value
    if "total value" in text or "inventory value" in text or "worth" in text:
        total_value = (
            db.query(func.coalesce(func.sum(StockLevel.quantity * Item.unit_price), 0))
            .join(Item, Item.id == StockLevel.item_id)
            .scalar()
            or 0
        )
        return {
            "answer": f"Your total inventory is currently worth ${float(total_value):,.2f}."
        }

    # Intent: warehouse count / list
    if "warehouse" in text and ("how many" in text or "list" in text):
        warehouses = db.query(Warehouse).all()
        return {
            "answer": f"You have {len(warehouses)} warehouse(s):",
            "list": [
                f"{w.code} — {w.name} ({w.location or 'no location set'})"
                for w in warehouses
            ],
        }

    # Intent: item count
    if "how many items" in text or "total items" in text:
        count = db.query(func.count(Item.id)).scalar() or 0
        return {"answer": f"You currently have {count} items tracked in StockLoom."}

    # Fallback
    return {
        "answer": "I'm not sure how to answer that yet. Try asking things like:",
        "list": [
            "'low stock items'",
            "'where is SKU-052'",
            "'total inventory value'",
            "'how many warehouses'",
            "'how long until SKU-052 runs out'",
            "'supplier for SKU-052'",
            "'open purchase orders'",
            "'top value items'",
        ],
    }

    # Intent: forecasting / days until stockout
    if any(kw in text for kw in ["days until", "stockout", "how long", "run out"]):
        from app.models.stock import StockMovement, MovementType
        from datetime import datetime, timedelta, timezone

        sku_match2 = re.search(r"sku[-\s]?(\w+)", text)
        if sku_match2:
            search_term = sku_match2.group(0).replace(" ", "-").upper()
            item = db.query(Item).filter(Item.sku.ilike(f"%{search_term}%")).first()
            if item:
                cutoff = datetime.now(timezone.utc) - timedelta(days=30)
                outbound = (
                    db.query(func.coalesce(func.sum(StockMovement.quantity), 0))
                    .filter(
                        StockMovement.item_id == item.id,
                        StockMovement.movement_type == MovementType.OUTBOUND,
                        StockMovement.created_at >= cutoff,
                    )
                    .scalar()
                    or 0
                )
                qty = totals.get(item.id, 0)
                velocity = outbound / 30
                if velocity <= 0:
                    return {
                        "answer": f"{item.sku} has no recent outbound movement, so I can't estimate a stockout date."
                    }
                days = round(qty / velocity, 1)
                return {
                    "answer": f"{item.sku} ({item.name}) has about {days} days of stock left at current usage rate."
                }
        return {
            "answer": "Tell me a SKU to check, e.g. 'how long until SKU-052 runs out'."
        }

    # Intent: supplier lookup
    if "supplier" in text:
        sku_match3 = re.search(r"sku[-\s]?(\w+)", text)
        if sku_match3:
            search_term = sku_match3.group(0).replace(" ", "-").upper()
            item = db.query(Item).filter(Item.sku.ilike(f"%{search_term}%")).first()
            if item and item.supplier:
                return {
                    "answer": f"{item.sku} is supplied by {item.supplier.name} ({item.supplier.contact_email or 'no email on file'})."
                }
            elif item:
                return {"answer": f"{item.sku} has no supplier assigned."}
        if "list" in text or "how many" in text:
            from app.models.organization import Supplier as SupplierModel

            suppliers = db.query(SupplierModel).all()
            return {
                "answer": f"You have {len(suppliers)} supplier(s):",
                "list": [s.name for s in suppliers],
            }

    # Intent: purchase order status
    if "purchase order" in text or " po " in text or text.startswith("po "):
        from app.models.purchase_order import PurchaseOrder

        po_match = re.search(r"po[-\s]?(\S+)", text)
        if po_match:
            po_number = po_match.group(1).upper()
            po = (
                db.query(PurchaseOrder)
                .filter(PurchaseOrder.po_number.ilike(f"%{po_number}%"))
                .first()
            )
            if po:
                return {
                    "answer": f"PO {po.po_number} is currently '{po.status.value}' with {len(po.lines)} line item(s)."
                }
            return {
                "answer": f"I couldn't find a purchase order matching '{po_number}'."
            }
        open_pos = (
            db.query(PurchaseOrder)
            .filter(PurchaseOrder.status.in_(["draft", "ordered"]))
            .all()
        )
        if not open_pos:
            return {"answer": "There are no open purchase orders right now."}
        return {
            "answer": f"You have {len(open_pos)} open purchase order(s):",
            "list": [f"{po.po_number} — {po.status.value}" for po in open_pos[:10]],
        }

    # Intent: ABC classification
    if "abc" in text or "top value" in text or "most valuable" in text:
        item_values = []
        for item in db.query(Item).all():
            qty = totals.get(item.id, 0)
            item_values.append((item, float(item.unit_price) * qty))
        item_values.sort(key=lambda x: x[1], reverse=True)
        top5 = item_values[:5]
        return {
            "answer": "Your top 5 highest-value items are:",
            "list": [f"{i.sku} — ${v:,.2f}" for i, v in top5],
        }

    # Fallback
    return {"answer": "I'm not sure how to help with that."}
