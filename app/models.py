from datetime import datetime
from pydantic import BaseModel


class SensorReading(BaseModel):
    device_id: str
    sensor_type: str
    value: float
    unit: str
    timestamp: datetime = datetime.now()
