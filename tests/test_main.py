import pytest
from fastapi.testclient import TestClient

from app.main import app, calculate_discount

client = TestClient(app)


# --- UNIT TESTS (Testing isolated functions) ---
def test_calculate_discount_valid():
    assert calculate_discount(100.0, 20) == 80.0
    assert calculate_discount(50.0, 0) == 50.0


def test_calculate_discount_invalid():
    with pytest.raises(ValueError):
        calculate_discount(100.0, 150)


# --- INTEGRATION TESTS (Testing API endpoints & HTTP status codes) ---
def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "inventory-api"}


def test_get_existing_product():
    response = client.get("/products/1")
    assert response.status_code == 200
    assert response.json()["name"] == "Mechanical Keyboard"


def test_get_nonexistent_product():
    response = client.get("/products/999")
    assert response.status_code == 404


def test_create_product():
    payload = {"name": "USB-C Hub", "price": 45.50, "stock": 10}
    response = client.post("/products", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "USB-C Hub"
    assert "id" in data