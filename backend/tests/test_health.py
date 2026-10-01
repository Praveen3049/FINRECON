from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "platform" in data
    assert data["platform"] == "FinRecon API"
    assert "docs_url" in data


def test_health_check_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert data["app_name"] == "FinRecon API"
    assert "database_connected" in data
    assert "supported_sources" in data
    assert "BANK" in data["supported_sources"]
    assert "CRYPTO" in data["supported_sources"]
