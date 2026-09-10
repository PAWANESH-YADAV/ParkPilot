from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "ParkPilot API" in data["message"]

def test_health():
    response = client.get("/health")
    assert response.status_code == 200

def test_parking_lots_endpoint():
    response = client.get("/api/v1/parkinglots")
    assert response.status_code == 200
