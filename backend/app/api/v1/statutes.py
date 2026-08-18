from fastapi import APIRouter
from app.schemas.statutes import StatuteMapResponse
from app.services.statutes_service import map_statute

router = APIRouter()

@router.get("/map", response_model=StatuteMapResponse)
def statute_map(section: str):
    """
    Cross-reference a statute section between IPC and BNS.
    Example: ?section=302  or  ?section=IPC+420
    """
    return map_statute(section)
