from datetime import datetime
from pydantic import BaseModel, Field


class SensorReading(BaseModel):
    device_id: str
    sensor_type: str
    value: float
    unit: str
    timestamp: datetime = Field(default_factory=datetime.now)
