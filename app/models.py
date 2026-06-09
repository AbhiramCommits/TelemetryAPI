from datetime import datetime
from typing import List
from pydantic import BaseModel, Field


class SensorReading(BaseModel):
    device_id: str
    sensor_type: str
    value: float
    unit: str
    timestamp: datetime = Field(default_factory=datetime.now)


class SensorReadingResponse(SensorReading):
    id: int


class BulkSensorReading(BaseModel):
    readings: List[SensorReading] = Field(..., min_length=1, max_length=500)


class BulkIngestionResult(BaseModel):
    total_received: int
    total_saved: int
    errors: List[str]
