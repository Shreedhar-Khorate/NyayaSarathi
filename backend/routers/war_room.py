from fastapi import APIRouter
from schemas.war_room import WarRoomRequest, WarRoomResponse
from services.war_room_service import simulate_war_room

router = APIRouter()


@router.post("/simulate", response_model=WarRoomResponse)
def war_room_simulate(request: WarRoomRequest):
    """Simulate adversarial opposition arguments against a given legal position."""
    return simulate_war_room(request)
