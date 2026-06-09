from fastapi import FastAPI
from app.routers import telemetry

app = FastAPI(title="TelemetryAPI")

app.include_router(telemetry.router)


@app.get("/")
def health_check():
    return {"status": "ok"}
