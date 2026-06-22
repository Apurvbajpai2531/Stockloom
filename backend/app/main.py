from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import Base, engine
from app.core.config import settings
from app.routers import organization, items, stock, dashboard

# Create tables if they don't exist (use Alembic migrations for production-grade workflows)
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.APP_NAME, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(organization.router, prefix="/api", tags=["organization"])
app.include_router(items.router, prefix="/api", tags=["items"])
app.include_router(stock.router, prefix="/api", tags=["stock"])
app.include_router(dashboard.router, prefix="/api", tags=["dashboard"])


@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": settings.APP_NAME}
