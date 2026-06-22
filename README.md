# StockLoom

Inventory & warehouse management system.

- **Backend:** FastAPI + SQLAlchemy (`backend/`)
- **Frontend:** NiceGUI, pure Python UI (`frontend/`)
- **Database:** PostgreSQL (schema auto-created from SQLAlchemy models)

> Docker and CI/CD are intentionally **not** included — that part is being handled separately.

## Project layout

```
stockloom/
├── backend/
│   └── app/
│       ├── core/        # settings, db session
│       ├── models/      # SQLAlchemy ORM models (Item, Warehouse, StockLevel, StockMovement, ...)
│       ├── schemas/      # Pydantic request/response models
│       ├── routers/      # API endpoints (items, organization, stock, dashboard)
│       └── main.py       # FastAPI app entrypoint
├── frontend/
│   ├── pages/             # Dashboard, Items, Warehouses, Stock Movements
│   ├── components.py      # shared nav header
│   ├── api_client.py       # thin requests wrapper around the backend API
│   └── main.py             # NiceGUI entrypoint
└── database/
    └── seed.py             # demo data seeder
```

## Data model

- **Warehouse** — physical locations
- **Category / Supplier** — item metadata
- **Item** — SKU, name, unit price, reorder threshold
- **StockLevel** — current quantity of an item at a warehouse (unique per item+warehouse)
- **StockMovement** — full audit trail: inbound, outbound, transfer (between warehouses), adjustment (set absolute quantity)

## Running locally (manual, no Docker)

1. **Start PostgreSQL** and create a database/user matching `DATABASE_URL` (default: `postgresql+psycopg2://stockloom:stockloom@localhost:5432/stockloom`), e.g.:
   ```sql
   CREATE USER stockloom WITH PASSWORD 'stockloom';
   CREATE DATABASE stockloom OWNER stockloom;
   ```

2. **Backend**
   ```bash
   cd backend
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   export DATABASE_URL=postgresql+psycopg2://stockloom:stockloom@localhost:5432/stockloom
   uvicorn app.main:app --reload --port 8000
   ```
   API docs at http://localhost:8000/docs

3. **Seed demo data (optional)**
   ```bash
   export DATABASE_URL=postgresql+psycopg2://stockloom:stockloom@localhost:5432/stockloom
   python database/seed.py
   ```

4. **Frontend**
   ```bash
   cd frontend
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   export API_BASE_URL=http://localhost:8000/api
   python main.py
   ```
   UI at http://localhost:8080

## API overview

| Method | Path | Description |
|---|---|---|
| GET/POST | `/api/items` | list/create items (supports `search`, `category_id`, `low_stock_only`) |
| PUT/DELETE | `/api/items/{id}` | update/delete an item |
| GET/POST | `/api/warehouses` | list/create warehouses |
| GET/POST | `/api/categories`, `/api/suppliers` | metadata CRUD |
| GET | `/api/stock-levels` | current quantities, filterable by item/warehouse |
| GET/POST | `/api/stock-movements` | history / record inbound, outbound, transfer, adjustment |
| GET | `/api/dashboard/summary` | totals: items, warehouses, units, value, low-stock count |

## Next steps (left for you)

- Dockerfiles for `backend/` and `frontend/`, plus `docker-compose.yml` wiring up Postgres
- CI pipeline (lint/test/build)
- Auth, if needed
- Alembic migrations (currently tables are created via `Base.metadata.create_all`)
