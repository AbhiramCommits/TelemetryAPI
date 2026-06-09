from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.models import SensorReading
from app.database import SensorReadingORM, get_db

router = APIRouter(prefix="/readings", tags=["telemetry"])


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_reading(reading: SensorReading, db: Session = Depends(get_db)):
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
    return {
        "id": db_reading.id,
        "device_id": db_reading.device_id,
        "sensor_type": db_reading.sensor_type,
        "value": db_reading.value,
        "unit": db_reading.unit,
        "timestamp": db_reading.timestamp,
    }


@router.get("/")
async def get_readings(
    device_id: str = Query(None),
    sensor_type: str = Query(None),
    limit: int = Query(100),
    db: Session = Depends(get_db),
):
    query = db.query(SensorReadingORM)
    if device_id:
        query = query.filter(SensorReadingORM.device_id == device_id)
    if sensor_type:
        query = query.filter(SensorReadingORM.sensor_type == sensor_type)
    readings = query.limit(limit).all()
    return [
        {
            "id": r.id,
            "device_id": r.device_id,
            "sensor_type": r.sensor_type,
            "value": r.value,
            "unit": r.unit,
            "timestamp": r.timestamp,
        }
        for r in readings
    ]


@router.get("/{device_id}/latest")
async def get_latest_reading(device_id: str, db: Session = Depends(get_db)):
    reading = (
        db.query(SensorReadingORM)
        .filter(SensorReadingORM.device_id == device_id)
        .order_by(SensorReadingORM.timestamp.desc(), SensorReadingORM.id.desc())
        .first()
    )
    if not reading:
        raise HTTPException(status_code=404, detail="Device not found")
    return {
        "id": reading.id,
        "device_id": reading.device_id,
        "sensor_type": reading.sensor_type,
        "value": reading.value,
        "unit": reading.unit,
        "timestamp": reading.timestamp,
    }
