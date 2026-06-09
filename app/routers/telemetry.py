import asyncio
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.models import SensorReading, SensorReadingResponse, BulkSensorReading, BulkIngestionResult
from app.database import SensorReadingORM, SessionLocal, get_db

router = APIRouter(prefix="/readings", tags=["telemetry"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=SensorReadingResponse)
async def create_reading(reading: SensorReading, db: Session = Depends(get_db)):
    """Ingest a single sensor reading and persist it to the database."""
    db_reading = SensorReadingORM(
        device_id=reading.device_id,
        sensor_type=reading.sensor_type,
        value=reading.value,
        unit=reading.unit,
        timestamp=reading.timestamp,
    )
    db.add(db_reading)
    db.commit()
    db.refresh(db_reading)
    return db_reading


@router.get("/", response_model=list[SensorReadingResponse])
async def get_readings(
    device_id: str = Query(None, description="Filter readings by device identifier"),
    sensor_type: str = Query(None, description="Filter readings by sensor type"),
    limit: int = Query(100, description="Maximum number of readings to return"),
    db: Session = Depends(get_db),
):
    """Retrieve stored sensor readings with optional device and sensor type filters."""
    query = db.query(SensorReadingORM)
    if device_id:
        query = query.filter(SensorReadingORM.device_id == device_id)
    if sensor_type:
        query = query.filter(SensorReadingORM.sensor_type == sensor_type)
    readings = query.limit(limit).all()
    return readings


@router.get("/{device_id}/latest", response_model=SensorReadingResponse)
async def get_latest_reading(device_id: str, db: Session = Depends(get_db)):
    """Return the most recent reading for the specified device."""
    reading = (
        db.query(SensorReadingORM)
        .filter(SensorReadingORM.device_id == device_id)
        .order_by(SensorReadingORM.timestamp.desc(), SensorReadingORM.id.desc())
        .first()
    )
    if not reading:
        raise HTTPException(status_code=404, detail="Device not found")
    return reading


async def _insert_one(reading: SensorReading):
    """Insert a single reading in its own database session."""
    await asyncio.sleep(0)
    db = SessionLocal()
    try:
        db_reading = SensorReadingORM(
            device_id=reading.device_id,
            sensor_type=reading.sensor_type,
            value=reading.value,
            unit=reading.unit,
            timestamp=reading.timestamp,
        )
        db.add(db_reading)
        db.commit()
        db.refresh(db_reading)
        return db_reading
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


@router.post("/bulk", status_code=207, response_model=BulkIngestionResult)
async def create_readings_bulk(bulk: BulkSensorReading):
    """Ingest a batch of sensor readings (1–500) concurrently. Per-record failures are collected without aborting the entire batch."""
    tasks = [_insert_one(reading) for reading in bulk.readings]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    total_received = len(bulk.readings)
    errors: list[str] = []
    total_saved = 0
    for idx, result in enumerate(results):
        if isinstance(result, Exception):
            errors.append(f"Reading {idx}: {result}")
        else:
            total_saved += 1

    return BulkIngestionResult(
        total_received=total_received,
        total_saved=total_saved,
        errors=errors,
    )
