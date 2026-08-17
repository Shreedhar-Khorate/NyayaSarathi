from pydantic import BaseModel
from typing import List


class WarRoomRequest(BaseModel):
    position: str
    rounds: int = 3

class WarRoomResponse(BaseModel):
    counter_arguments: List[str]
    weaknesses_identified: List[str]
    suggested_reinforcements: List[str]
