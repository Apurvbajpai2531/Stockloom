import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("stockloom")

from app.core.database import Base, engine
from app.core.config import settings
from app.routers import organization, items, stock, dashboard, purchase_orders, alerts, reports, auth, audit, qrcodes, forecasting, notifications, ws

# Create tables if they don't exist (use Alembic migrations for production-grade workflows)
Base.metadata.create_all(bind=engine)

from app.core.database import SessionLocal
from app.core.auth import ensure_default_admin

_db = SessionLocal()
ensure_default_admin(_db)
_db.close()

app = FastAPI(title=settings.APP_NAME, version="1.0.0")

import os

allowed_origins = os.getenv("CORS_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi import Depends
from app.core.auth import get_current_user

protected = [Depends(get_current_user)]

app.include_router(organization.router, prefix="/api", tags=["organization"], dependencies=protected)
app.include_router(items.router, prefix="/api", tags=["items"], dependencies=protected)
app.include_router(stock.router, prefix="/api", tags=["stock"], dependencies=protected)
app.include_router(dashboard.router, prefix="/api", tags=["dashboard"], dependencies=protected)
app.include_router(purchase_orders.router, prefix="/api", tags=["purchase-orders"], dependencies=protected)
app.include_router(alerts.router, prefix="/api", tags=["alerts"], dependencies=protected)
app.include_router(reports.router, prefix="/api", tags=["reports"], dependencies=protected)
app.include_router(auth.router, prefix="/api", tags=["auth"])  # login itself stays open
app.include_router(audit.router, prefix="/api", tags=["audit"], dependencies=protected)
app.include_router(qrcodes.router, prefix="/api", tags=["qrcodes"])  # public - just renders a QR image, no sensitive data
app.include_router(forecasting.router, prefix="/api", tags=["forecasting"], dependencies=protected)
app.include_router(notifications.router, prefix="/api", tags=["notifications"], dependencies=protected)
app.include_router(ws.router, prefix="/api", tags=["websocket"])  # no auth dependency — WS auth handled differently


@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": settings.APP_NAME}



@app.exception_handler(SQLAlchemyError)
async def db_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.error(f"Database error on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "A database error occurred. Please try again."},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred."},
    )


@app.middleware("http")
async def log_requests(request: Request, call_next):
    response = await call_next(request)
    logger.info(f"{request.method} {request.url.path} -> {response.status_code}")
    return response
