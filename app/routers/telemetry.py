from fastapi import APIRouter

router = APIRouter(prefix="/readings", tags=["telemetry"])


@router.post("/")
def create_reading():
    return {"message": "not yet implemented"}
