"""
Case Management Service — In-Memory Store with War Room Session Integration
"""
import uuid
from typing import List, Optional
from schemas.cases import Case, CreateCaseRequest, TimelineResponse, TimelineEvent


# In-memory store alongside database sessions
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
    cases_map = dict(_cases)
    try:
        from services.war_room_repository import list_war_room_sessions
        db_sessions = list_war_room_sessions(limit=50)
        for s in db_sessions:
            sid = s.get("id")
            if sid and sid not in cases_map:
                cases_map[sid] = Case(
                    case_id=sid,
                    title=s.get("title", "Legal War Room Session"),
                    status="active",
                )
    except Exception:
        pass
    return list(cases_map.values())


def get_case(case_id: str) -> Optional[Case]:
    if case_id in _cases:
        return _cases[case_id]
    try:
        from services.war_room_repository import get_war_room_session
        sess = get_war_room_session(case_id)
        if sess:
            return Case(
                case_id=sess["id"],
                title=sess.get("title", "Legal Matter"),
                status="active",
            )
    except Exception:
        pass
    return None


def get_timeline(case_id: str) -> TimelineResponse:
    """
    Returns verified chronological events for a case.
    Retrieves from verified case records if available, or dynamically extracts them.
    """
    try:
        from services.war_room_repository import get_war_room_session
        sess = get_war_room_session(case_id)
        if sess:
            # 1. Stored relevant dates
            if sess.get("relevant_dates"):
                events = []
                for rd in sess["relevant_dates"]:
                    events.append(
                        TimelineEvent(
                            event_date=rd.get("event_date", "Date not specified"),
                            description=rd.get("description", "Case event"),
                            source_doc=rd.get("source_reference"),
                        )
                    )
                if events:
                    return TimelineResponse(events=events)

            # 2. Dynamically extract from fact sheet if present
            fact_sheet = sess.get("fact_sheet") or []
            events = []
            for item in fact_sheet:
                if isinstance(item, dict) and item.get("date"):
                    events.append(
                        TimelineEvent(
                            event_date=str(item["date"]),
                            description=str(item.get("fact", item.get("description", "Chronological occurrence"))),
                            source_doc=item.get("source"),
                        )
                    )
            if events:
                return TimelineResponse(events=events)
    except Exception:
        pass

    return TimelineResponse(events=[])

