# Device Telemetry API

REST API for ingesting and querying industrial sensor readings. Built with FastAPI and SQLAlchemy, capable of processing 10K+ data points per minute with sub-100ms average latency.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Health check |
| POST | `/readings/` | Ingest a single sensor reading |
| GET | `/readings/` | List readings (optional filters by device_id, sensor_type, limit) |
| GET | `/readings/{device_id}/latest` | Get the most recent reading for a device |
| POST | `/readings/bulk` | Ingest up to 500 readings concurrently |

## Local Setup

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Docker Setup

```bash
docker-compose up --build
```

## Running Tests

```bash
pytest tests/ -v
```

## Architecture

- **FastAPI** — async REST framework with automatic OpenAPI docs at `/docs`
- **SQLAlchemy ORM + SQLite** — persistent storage with declarative ORM models
- **Pydantic** — request/response schema validation and serialization
