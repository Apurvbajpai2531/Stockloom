# StockLoom — Inventory & Warehouse Management

StockLoom is a full-stack inventory and warehouse management system built with **FastAPI**, **NiceGUI**, and **PostgreSQL** for managing stock, warehouse operations, purchasing, and inventory analytics.

## Tech Stack

* **Backend:** FastAPI + SQLAlchemy + PostgreSQL
* **Frontend:** NiceGUI
* **Auth:** JWT + Role-Based Access

## Features

* Inventory, Items & Warehouse Management
* Stock Movements (Inbound / Outbound / Transfer / Adjustment)
* Purchase Orders & Auto Stock Updates
* Dashboard, Reports & Analytics
* Low Stock Alerts & Reorder Suggestions
* Stock Forecasting & ABC Analysis
* JWT Authentication & Role Management
* Audit Logs, Notifications & QR Support
* Responsive UI with Dark Mode & Command Palette

## Run Locally

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
pip install -r requirements.txt
python3 main.py
```

Backend → `http://localhost:8000/docs`
Frontend → `http://localhost:8081`

## Default Login

```text
Username: admin
Password: stockloom123
```

Production-inspired inventory architecture with secure stock operations, analytics, and warehouse orchestration.
