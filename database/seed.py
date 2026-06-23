"""
Seed the StockLoom database with demo data.
Run: python database/seed.py
"""
import sys
import os
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.core.database import SessionLocal, Base, engine
from app.models.organization import Warehouse, Category, Supplier
from app.models.item import Item
from app.models.stock import StockLevel

Base.metadata.create_all(bind=engine)
db = SessionLocal()

if db.query(Warehouse).count() == 0:
    # -------------------
    # Warehouses
    # -------------------
    warehouses = [
        Warehouse(name="Main Warehouse", code="WH-MAIN", location="Delhi, IN"),
        Warehouse(name="North Depot", code="WH-NORTH", location="Chandigarh, IN"),
        Warehouse(name="South Hub", code="WH-SOUTH", location="Bangalore, IN"),
        Warehouse(name="West Storage", code="WH-WEST", location="Mumbai, IN"),
        Warehouse(name="East Yard", code="WH-EAST", location="Kolkata, IN"),
    ]
    db.add_all(warehouses)
    db.flush()

    # -------------------
    # Categories
    # -------------------
    categories = [
        Category(name="Electronics", description="Electronic devices"),
        Category(name="Hardware", description="Bolts and fasteners"),
        Category(name="Networking", description="Network equipment"),
        Category(name="Accessories", description="General accessories"),
        Category(name="Office", description="Office inventory"),
        Category(name="Storage", description="Storage and drives"),
    ]
    db.add_all(categories)
    db.flush()

    # -------------------
    # Suppliers
    # -------------------
    suppliers = [
        Supplier(name=f"Supplier {i}", contact_email=f"supplier{i}@demo.com",
                 contact_phone=f"+91-90000000{i:02}")
        for i in range(1, 9)
    ]
    db.add_all(suppliers)
    db.flush()

    # -------------------
    # Product templates
    # -------------------
    product_names = [
        "USB Cable", "HDMI Cable", "Keyboard", "Mouse", "Monitor",
        "Router", "Switch", "SSD", "Laptop Stand", "Power Adapter",
        "Webcam", "Headset", "Docking Station", "External HDD", "Printer",
        "Scanner", "UPS Unit", "Network Cable", "Surge Protector", "Tablet Stand",
    ]

    items = []
    for i in range(1, 121):  # 120 items
        category = random.choice(categories)
        supplier = random.choice(suppliers)
        item = Item(
            sku=f"SKU-{i:03}",
            name=f"{random.choice(product_names)} {i}",
            unit="pcs",
            unit_price=round(random.uniform(2, 500), 2),
            reorder_threshold=random.randint(20, 300),
            category_id=category.id,
            supplier_id=supplier.id,
        )
        items.append(item)
    db.add_all(items)
    db.flush()

    # -------------------
    # Stock Levels (some items intentionally low-stock for dashboard testing)
    # -------------------
    stock = []
    for item in items:
        selected_wh = random.sample(warehouses, random.randint(1, len(warehouses)))
        for wh in selected_wh:
            # ~15% chance of low stock to populate "low stock" widgets meaningfully
            qty = random.randint(0, item.reorder_threshold) if random.random() < 0.15 \
                else random.randint(item.reorder_threshold, 1000)
            stock.append(StockLevel(item_id=item.id, warehouse_id=wh.id, quantity=qty))
    db.add_all(stock)
    db.commit()

    print("Seed completed")
    print(f"Warehouses : {len(warehouses)}")
    print(f"Categories : {len(categories)}")
    print(f"Suppliers  : {len(suppliers)}")
    print(f"Items      : {len(items)}")
    print(f"Stock Rows : {len(stock)}")
else:
    print("Database already has data, skipping seed.")

db.close()