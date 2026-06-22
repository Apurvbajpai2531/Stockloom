import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "StockLoom"
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://stockloom:stockloom@localhost:5432/stockloom",
    )
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-this-secret-key")
    LOW_STOCK_DEFAULT_THRESHOLD: int = 10

    class Config:
        env_file = ".env"


settings = Settings()
