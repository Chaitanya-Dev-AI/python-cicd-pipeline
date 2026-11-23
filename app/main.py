import logging
import time
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.config import settings
from app.database import ProductDB, check_db_health, get_db, init_db

logging.basicConfig(
    level=settings.log_level,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}',
)
logger = logging.getLogger("inventory-api")

DbSession = Annotated[Session, Depends(get_db)]


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.app_name} in {settings.environment} mode")
    init_db()
    yield
    logger.info("Shutting down service cleanly")


app = FastAPI(title=settings.app_name, version="2.0.0", lifespan=lifespan)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
    logger.info(
        f"{request.method} {request.url.path} - Status: {response.status_code} - {duration_ms}ms"
    )
    return response


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    price: float = Field(..., gt=0)
    stock: int = Field(..., ge=0)


class ProductResponse(ProductCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)


@app.get("/health")
def health_check():
    """Liveness probe: confirms the web server is running."""
    return {
        "status": "healthy",
        "service": "inventory-api",
        "environment": settings.environment,
    }


@app.get("/ready")
def readiness_check():
    """Readiness probe: confirms database connectivity before receiving traffic."""
    if not check_db_health():
        raise HTTPException(status_code=503, detail="Database unavailable")
    return {"status": "ready", "database": "connected"}


@app.get("/products", response_model=list[ProductResponse])
def list_products(db: DbSession):
    return db.query(ProductDB).all()


@app.get("/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: DbSession):
    product = db.query(ProductDB).filter(ProductDB.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.post("/products", response_model=ProductResponse, status_code=201)
def create_product(product: ProductCreate, db: DbSession):
    db_product = ProductDB(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


def calculate_discount(price: float, discount_percent: float) -> float:
    if not 0 <= discount_percent <= 100:
        raise ValueError("Discount must be between 0 and 100")
    return round(price * (1 - discount_percent / 100), 2)