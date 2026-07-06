# StockLoom — Inventory & Warehouse Management

StockLoom is a full-stack inventory and warehouse management system built with **FastAPI**, **NiceGUI**, and **PostgreSQL** for managing stock, warehouse operations, purchasing, and inventory analytics.

---

## Tech Stack

- Backend: FastAPI + SQLAlchemy + PostgreSQL  
- Frontend: NiceGUI  
- Auth: JWT + Role-Based Access  

---

## Features

- Inventory, Items & Warehouse Management  
- Stock Movements (Inbound / Outbound / Transfer / Adjustment)  
- Purchase Orders & Auto Stock Updates  
- Dashboard, Reports & Analytics  
- Low Stock Alerts & Reorder Suggestions  
- Stock Forecasting & ABC Analysis  
- JWT Authentication & Role Management  
- Audit Logs, Notifications & QR Support  
- Responsive UI with Dark Mode & Command Palette  

---

## Run Locally

Backend:
cd backend
python -m venv virtual_environment_name
pip install -r requirements.txt
uvicorn app.main:app --reload

Frontend:
cd frontend
python -m venv virtual_environment_name
pip install -r requirements.txt
python3 main.py

---

## Docker Compose (Recommended)

Run full stack using Docker:

docker compose up --build

Stop services:

docker compose down

---

## Access URLs

Frontend UI:
http://localhost:8081

Backend API Docs:
http://localhost:8000/docs

---

## Default Login (UI Access)

Open frontend and login using:

Username: admin  
Password: stockloom123  

---

---

## Overview

StockLoom is designed with production-grade architecture for secure inventory control, warehouse orchestration, and analytics-driven decision making.
