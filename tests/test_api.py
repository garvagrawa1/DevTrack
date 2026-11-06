from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_homepage():
    response = client.get("/")
    assert response.status_code == 200
    assert "Understand the work" in response.text


def test_openapi_available():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert "repository" in response.text
