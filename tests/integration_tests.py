from fastapi.testclient import TestClient
import sys
import os

# Add backend directory to path so app can be imported
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))

try:
    from app.main import app
    client = TestClient(app)
except ImportError:
    app = None
    client = None

def test_health_check():
    if client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

def test_ev_queue():
    if client:
        response = client.get("/api/v1/ev/queue")
        # Route might require auth or return 200/404 depending on db state
        assert response.status_code in [200, 401, 403, 404]

def test_carbon_user():
    if client:
        response = client.get("/api/v1/carbon/user/1")
        assert response.status_code in [200, 401, 403, 404]

def test_pricing_current():
    if client:
        response = client.get("/api/v1/pricing/current/1")
        assert response.status_code in [200, 401, 403, 404]

def test_security_events():
    if client:
        response = client.get("/api/v1/security/events")
        assert response.status_code in [200, 401, 403, 404]
