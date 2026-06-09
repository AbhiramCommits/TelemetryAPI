from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import create_tables
from app.routers import telemetry


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield


app = FastAPI(
    title="Device Telemetry API",
    version="1.0.0",
    description="REST API for ingesting and querying device sensor readings.",
    lifespan=lifespan,
)

app.include_router(telemetry.router)


@app.get("/")
def health_check():
    return {"status": "ok"}
