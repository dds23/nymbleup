from fastapi.testclient import TestClient
from main import app
import pytest

client = TestClient(app)


def test_fetch_item_details():
    response = client.get('/items')
    assert response.status_code == 200


def test_add_sales():
    sales_data = [{"item_code": "13887490", "quantity": 2},
                  {"item_code": "25026597", "quantity": 1}]
    response = client.post('/sales', json=sales_data)
    assert response.status_code == 200
    assert response.json()["message"] == "Sales added successfully"


def test_fetch_sales_summary():
    response = client.get('/sales-summary?date=2024-08-07')
    assert response.status_code == 200
    assert "summary" in response.json()
    assert "total_sales" in response.json()
