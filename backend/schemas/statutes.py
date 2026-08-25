from pydantic import BaseModel


class StatuteMapResponse(BaseModel):
    input_section: str
    mapped_section: str
    notes: str
