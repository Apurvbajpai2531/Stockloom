from app.core.audit import log_action
from app.core.auth import get_current_user
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.models.item import Item
from app.models.stock import StockLevel
from app.schemas.item import ItemCreate, ItemUpdate, ItemOut, ItemWithStock


router = APIRouter()


@router.get("/items", response_model=list[ItemWithStock])
def list_items(
    db: Session = Depends(get_db),
    search: str | None = Query(default=None, description="Search by name or SKU"),
    category_id: int | None = None,
    low_stock_only: bool = False,
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
):
    q = db.query(Item)
    if search:
        like = f"%{search}%"
        q = q.filter((Item.name.ilike(like)) | (Item.sku.ilike(like)))
    if category_id:
        q = q.filter(Item.category_id == category_id)

    items = q.order_by(Item.name).offset(offset).limit(limit).all()

    totals = dict(
        db.query(StockLevel.item_id, func.coalesce(func.sum(StockLevel.quantity), 0))
        .group_by(StockLevel.item_id)
        .all()
    )

    result = []
    for it in items:
        total_qty = totals.get(it.id, 0)
        if low_stock_only and total_qty > it.reorder_threshold:
            continue
        out = ItemWithStock.model_validate(it)
        out.total_quantity = total_qty
        result.append(out)
    return result


@router.get("/items/{item_id}", response_model=ItemWithStock)
def get_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    total_qty = (
        db.query(func.coalesce(func.sum(StockLevel.quantity), 0))
        .filter(StockLevel.item_id == item_id)
        .scalar()
    )
    out = ItemWithStock.model_validate(item)
    out.total_quantity = total_qty or 0
    return out


@router.post("/items", response_model=ItemOut, status_code=201)
def create_item(payload: ItemCreate, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    item = Item(**payload.model_dump())
    db.add(item)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="SKU already exists")
    db.refresh(item)
    log_action(db, "create_item", "item", item.id, user, f"SKU={item.sku}, name={item.name}")
    return item

@router.put("/items/{item_id}", response_model=ItemOut)
def update_item(item_id: int, payload: ItemUpdate, db: Session = Depends(get_db)):
    item = db.query(Item).get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="SKU already exists")
    db.refresh(item)
    return item


@router.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: int, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    item = db.query(Item).get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    sku = item.sku
    db.delete(item)
    db.commit()
    log_action(db, "delete_item", "item", item_id, user, f"SKU={sku}")
