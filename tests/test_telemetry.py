from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_reading_placeholder():
    response = client.post("/readings/")
    assert response.status_code == 200
    assert response.json() == {"message": "not yet implemented"}
