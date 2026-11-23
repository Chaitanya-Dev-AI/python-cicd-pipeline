from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Inventory Microservice", version="1.0.0")

# In-memory database for demonstration
inventory_db: dict[int, dict] = {
    1: {"id": 1, "name": "Mechanical Keyboard", "price": 120.0, "stock": 15},
    2: {"id": 2, "name": "Wireless Mouse", "price": 60.0, "stock": 30},
}


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    price: float = Field(..., gt=0)
    stock: int = Field(..., ge=0)


@app.get("/health")
def health_check():
    """Used by CI/CD pipelines and load balancers to verify the app is alive."""
    return {"status": "healthy", "service": "inventory-api"}


@app.get("/products")
def list_products():
    return list(inventory_db.values())


@app.get("/products/{product_id}")
def get_product(product_id: int):
    if product_id not in inventory_db:
        raise HTTPException(status_code=404, detail="Product not found")
    return inventory_db[product_id]


@app.post("/products", status_code=201)
def create_product(product: ProductCreate):
    new_id = max(inventory_db.keys(), default=0) + 1
    new_item = {"id": new_id, **product.model_dump()}
    inventory_db[new_id] = new_item
    return new_item


def calculate_discount(price: float, discount_percent: float) -> float:
    """Pure business logic function to demonstrate unit testing."""
    if not 0 <= discount_percent <= 100:
        raise ValueError("Discount must be between 0 and 100")
    return round(price * (1 - discount_percent / 100), 2)