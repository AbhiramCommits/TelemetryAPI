import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, SessionLocal

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_reading():
    payload = {
        "device_id": "device-1",
        "sensor_type": "temperature",
        "value": 23.5,
        "unit": "celsius",
    }
    response = client.post("/readings/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["device_id"] == "device-1"
    assert data["sensor_type"] == "temperature"
    assert data["value"] == 23.5
    assert data["unit"] == "celsius"
    assert "timestamp" in data


def test_get_readings():
    for i in range(3):
        client.post(
            "/readings/",
            json={
                "device_id": f"device-{i % 2}",
                "sensor_type": "temperature",
                "value": 20.0 + i,
                "unit": "celsius",
            },
        )
    response = client.get("/readings/")
    assert response.status_code == 200
    assert len(response.json()) == 3


def test_get_readings_filtered_by_device():
    for i in range(3):
        client.post(
            "/readings/",
            json={
                "device_id": f"device-{i % 2}",
                "sensor_type": "temperature",
                "value": 20.0 + i,
                "unit": "celsius",
            },
        )
    response = client.get("/readings/?device_id=device-1")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["device_id"] == "device-1"


def test_get_readings_filtered_by_type():
    client.post("/readings/", json={"device_id": "d1", "sensor_type": "temp", "value": 1.0, "unit": "C"})
    client.post("/readings/", json={"device_id": "d2", "sensor_type": "humidity", "value": 50.0, "unit": "%"})
    response = client.get("/readings/?sensor_type=humidity")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["sensor_type"] == "humidity"


def test_get_readings_limit():
    for i in range(5):
        client.post("/readings/", json={"device_id": "d1", "sensor_type": "temp", "value": float(i), "unit": "C"})
    response = client.get("/readings/?limit=2")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_latest_reading():
    client.post("/readings/", json={"device_id": "d1", "sensor_type": "temp", "value": 10.0, "unit": "C"})
    client.post("/readings/", json={"device_id": "d1", "sensor_type": "temp", "value": 99.0, "unit": "C"})
    response = client.get("/readings/d1/latest")
    assert response.status_code == 200
    assert response.json()["value"] == 99.0


def test_get_latest_reading_not_found():
    response = client.get("/readings/nonexistent/latest")
    assert response.status_code == 404
    assert response.json()["detail"] == "Device not found"


def test_create_bulk_readings():
    payload = {
        "readings": [
            {"device_id": "dev-1", "sensor_type": "temp", "value": 22.0, "unit": "C"},
            {"device_id": "dev-2", "sensor_type": "humidity", "value": 60.0, "unit": "%"},
            {"device_id": "dev-3", "sensor_type": "pressure", "value": 1013.0, "unit": "hPa"},
        ]
    }
    response = client.post("/readings/bulk", json=payload)
    assert response.status_code == 207
    data = response.json()
    assert data["total_received"] == 3
    assert data["total_saved"] == 3
    assert data["errors"] == []


def test_create_bulk_empty_readings():
    response = client.post("/readings/bulk", json={"readings": []})
    assert response.status_code == 422


def test_create_bulk_single_reading():
    payload = {
        "readings": [
            {"device_id": "solo", "sensor_type": "light", "value": 400.0, "unit": "lux"},
        ]
    }
    response = client.post("/readings/bulk", json=payload)
    assert response.status_code == 207
    data = response.json()
    assert data["total_received"] == 1
    assert data["total_saved"] == 1
    assert data["errors"] == []
