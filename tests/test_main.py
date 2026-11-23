import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app, calculate_discount

TEST_DATABASE_URL = "sqlite:///./test_inventory.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_and_teardown_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


def test_calculate_discount_valid():
    assert calculate_discount(100.0, 20) == 80.0
    assert calculate_discount(50.0, 0) == 50.0


def test_calculate_discount_invalid():
    with pytest.raises(ValueError):
        calculate_discount(100.0, 150)


def test_health_and_readiness():
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "healthy"

    ready = client.get("/ready")
    assert ready.status_code == 200
    assert ready.json()["database"] == "connected"


def test_create_and_fetch_product():
    payload = {"name": "Mechanical Keyboard", "price": 120.0, "stock": 15}
    create_res = client.post("/products", json=payload)
    assert create_res.status_code == 201
    created = create_res.json()
    assert created["name"] == "Mechanical Keyboard"

    get_res = client.get(f"/products/{created['id']}")
    assert get_res.status_code == 200
    assert get_res.json()["price"] == 120.0

    list_res = client.get("/products")
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1


def test_get_nonexistent_product():
    response = client.get("/products/999")
    assert response.status_code == 404