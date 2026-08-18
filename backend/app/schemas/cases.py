from pydantic import BaseModel
from typing import List, Optional
from datetime import date


class Deadline(BaseModel):
    title: str
    due_date: date

class Case(BaseModel):
    case_id: str
    title: str
    status: str   # active | pending | closed
    deadlines: List[Deadline] = []
    team_members: List[str] = []

class CreateCaseRequest(BaseModel):
    title: str
    status: str = "active"

class TimelineEvent(BaseModel):
    event_date: str
    description: str
    source_doc: Optional[str] = None

class TimelineResponse(BaseModel):
    events: List[TimelineEvent]
