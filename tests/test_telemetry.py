import asyncio
import pytest
from starlette.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
import app.routers.telemetry as telemetry_module

# ── in-memory SQLite for test isolation ──────────────────────────────────
test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
telemetry_module.SessionLocal = TestSessionLocal

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


# ── helper ───────────────────────────────────────────────────────────────
def _valid_reading(device_id="d1", sensor_type="temp", value=20.0, unit="C", timestamp=None):
    reading = {"device_id": device_id, "sensor_type": sensor_type, "value": value, "unit": unit}
    if timestamp is not None:
        reading["timestamp"] = timestamp
    return reading


# ── health check ─────────────────────────────────────────────────────────
def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ── POST /readings ───────────────────────────────────────────────────────
def test_post_single_reading_success():
    payload = _valid_reading()
    response = client.post("/readings/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["device_id"] == payload["device_id"]
    assert data["sensor_type"] == payload["sensor_type"]
    assert data["value"] == payload["value"]
    assert data["unit"] == payload["unit"]
    assert "timestamp" in data


def test_post_reading_missing_field():
    payload = {"device_id": "d1", "sensor_type": "temp", "unit": "C"}
    response = client.post("/readings/", json=payload)
    assert response.status_code == 422


def test_post_reading_invalid_value_type():
    payload = _valid_reading(value="not-a-number")
    response = client.post("/readings/", json=payload)
    assert response.status_code == 422


# ── GET /readings ────────────────────────────────────────────────────────
def test_get_all_readings_empty():
    response = client.get("/readings/")
    assert response.status_code == 200
    assert response.json() == []


def test_get_readings_filter_by_device():
    for _ in range(3):
        client.post("/readings/", json=_valid_reading(device_id="A"))
    for _ in range(2):
        client.post("/readings/", json=_valid_reading(device_id="B"))
    response = client.get("/readings/?device_id=A")
    assert response.status_code == 200
    assert len(response.json()) == 3


def test_get_readings_limit():
    for i in range(10):
        client.post("/readings/", json=_valid_reading(value=float(i)))
    response = client.get("/readings/?limit=5")
    assert response.status_code == 200
    assert len(response.json()) == 5


# ── GET /readings/{device_id}/latest ─────────────────────────────────────
def test_get_latest_reading_exists():
    client.post(
        "/readings/",
        json=_valid_reading(device_id="dev", value=10.0, timestamp="2026-01-01T00:00:00"),
    )
    client.post(
        "/readings/",
        json=_valid_reading(device_id="dev", value=20.0, timestamp="2026-06-01T00:00:00"),
    )
    client.post(
        "/readings/",
        json=_valid_reading(device_id="dev", value=30.0, timestamp="2026-12-01T00:00:00"),
    )
    response = client.get("/readings/dev/latest")
    assert response.status_code == 200
    assert response.json()["value"] == 30.0


def test_get_latest_reading_not_found():
    response = client.get("/readings/nonexistent/latest")
    assert response.status_code == 404
    assert response.json()["detail"] == "Device not found"


# ── POST /readings/bulk ──────────────────────────────────────────────────
def test_bulk_ingestion_success():
    readings = [_valid_reading(device_id=f"dev-{i}") for i in range(10)]
    response = client.post("/readings/bulk", json={"readings": readings})
    assert response.status_code == 207
    data = response.json()
    assert data["total_received"] == 10
    assert data["total_saved"] == 10
    assert data["errors"] == []


def test_bulk_ingestion_partial_errors(monkeypatch):
    original = telemetry_module._insert_one

    async def _injecting_insert_one(reading):
        await asyncio.sleep(0)
        if reading.device_id in ("bad-1", "bad-2"):
            raise ValueError("Simulated DB error")
        return await original(reading)

    monkeypatch.setattr(telemetry_module, "_insert_one", _injecting_insert_one)

    readings = [_valid_reading(device_id=f"dev-{i}") for i in range(8)]
    readings.append(_valid_reading(device_id="bad-1"))
    readings.append(_valid_reading(device_id="bad-2"))

    response = client.post("/readings/bulk", json={"readings": readings})
    assert response.status_code == 207
    data = response.json()
    assert data["total_received"] == 10
    assert data["total_saved"] == 8
    assert len(data["errors"]) == 2
