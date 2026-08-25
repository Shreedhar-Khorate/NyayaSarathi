"""
Case Management Service — In-Memory Implementation
TODO: Replace with a real database (e.g. PostgreSQL via SQLAlchemy).
"""
import uuid
from typing import List, Optional
from schemas.cases import Case, CreateCaseRequest, TimelineResponse, TimelineEvent


# In-memory store (replace with DB)
_cases: dict[str, Case] = {}


def create_case(request: CreateCaseRequest) -> Case:
    case = Case(
        case_id=str(uuid.uuid4()),
        title=request.title,
        status=request.status,
    )
    _cases[case.case_id] = case
    return case


def list_cases() -> List[Case]:
    return list(_cases.values())


def get_case(case_id: str) -> Optional[Case]:
    return _cases.get(case_id)


def get_timeline(case_id: str) -> TimelineResponse:
    # Sample timeline — replace with DB + NLP extraction
    return TimelineResponse(
        events=[
            TimelineEvent(
                event_date="2024-01-10",
                description="FIR registered at Andheri Police Station.",
                source_doc="FIR_No_42_2024.pdf",
            ),
            TimelineEvent(
                event_date="2024-02-15",
                description="Charge sheet filed before JMFC Court.",
                source_doc="ChargeSheet_Feb2024.pdf",
            ),
            TimelineEvent(
                event_date="2024-04-03",
                description="Bail application filed and hearing scheduled.",
                source_doc=None,
            ),
        ]
    )
