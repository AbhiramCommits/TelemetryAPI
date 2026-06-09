from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from datetime import datetime

SQLALCHEMY_DATABASE_URL = "sqlite:///./telemetry.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class SensorReadingORM(Base):
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String, nullable=False)
    sensor_type = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.now)


Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
