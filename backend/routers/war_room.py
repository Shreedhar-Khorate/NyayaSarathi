"""
NyayaSarathi Legal War Room — API Router
Provides RESTful endpoints for session management, case configuration,
grounded fact extraction, evidence analysis, argument building, opposition simulation,
Indian precedent research, and strategy report export.
"""

import uuid
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Header, Response, status

from schemas.war_room import (
    WarRoomRequest,
    WarRoomResponse,
    WarRoomSessionCreate,
    WarRoomSessionUpdate,
    WarRoomSessionResponse,
    WarRoomAnalyzeRequest,
    WarRoomAnalyzeResponse,
)
from services.war_room_repository import (
    create_session,
    get_session_by_id,
    list_sessions,
    update_session,
    delete_session,
    get_session_usage_summary,
)
from services.war_room_service import (
    simulate_war_room,
    execute_war_room_analysis,
)
from services.auth_service import decode_access_token
from services.cases_service import get_case, get_timeline

router = APIRouter()


def get_optional_user_id(authorization: Optional[str] = Header(None)) -> Optional[str]:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ")[1]
    try:
        payload = decode_access_token(token)
        return payload.get("sub")
    except Exception:
        return None


# ── Session CRUD Endpoints ───────────────────────────────────────────────────

@router.post("", response_model=WarRoomSessionResponse, status_code=status.HTTP_201_CREATED)
def create_war_room_session(
    payload: WarRoomSessionCreate,
    user_id: Optional[str] = Depends(get_optional_user_id),
):
    """Creates a new War Room case workspace."""
    session_id = str(uuid.uuid4())
    
    title = payload.title.strip() if payload.title else ""
    dates = [d.model_dump() if hasattr(d, "model_dump") else d.dict() for d in (payload.relevant_dates or [])]
    
    # If case_id provided, import metadata from Cases module if not set
    if payload.case_id:
        existing_case = get_case(payload.case_id)
        if existing_case:
            if not title or title == "Untitled War Room":
                title = existing_case.title
            if not dates:
                timeline_data = get_timeline(payload.case_id)
                if timeline_data and timeline_data.events:
                    dates = [
                        {
                            "event_date": e.event_date,
                            "description": e.description,
                            "source_reference": e.source_doc,
                        }
                        for e in timeline_data.events
                    ]

    session_data = {
        "id": session_id,
        "user_id": user_id,
        "case_id": payload.case_id,
        "title": title or "Untitled War Room",
        "description": (payload.description or "").strip(),
        "case_type": payload.case_type or "general",
        "jurisdiction": payload.jurisdiction or "High Court",
        "court": (payload.court or "").strip(),
        "user_position": payload.user_position or "petitioner",
        "opposing_party": (payload.opposing_party or "").strip(),
        "relevant_dates": dates,
        "selected_doc_ids": payload.selected_doc_ids or [],
        "case_overview": {},
        "fact_sheet": [],
        "evidence_findings": [],
        "arguments": [],
        "opposition": [],
        "risks": [],
        "precedents": [],
        "report": {},
    }
    session = create_session(session_data)
    return session


@router.post("/from-case/{case_id}", response_model=WarRoomSessionResponse, status_code=status.HTTP_201_CREATED)
def create_war_room_from_case(
    case_id: str,
    user_id: Optional[str] = Depends(get_optional_user_id),
):
    """Convenience endpoint to initialize a War Room workspace directly from an existing case."""
    existing_case = get_case(case_id)
    if not existing_case:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")
    
    timeline_data = get_timeline(case_id)
    relevant_dates = []
    if timeline_data and timeline_data.events:
        relevant_dates = [
            {
                "event_date": e.event_date,
                "description": e.description,
                "source_reference": e.source_doc,
            }
            for e in timeline_data.events
        ]
    
    session_id = str(uuid.uuid4())
    session_data = {
        "id": session_id,
        "user_id": user_id,
        "case_id": case_id,
        "title": existing_case.title,
        "description": f"Imported from Case {case_id} ({existing_case.status})",
        "case_type": "general",
        "jurisdiction": "High Court",
        "court": "",
        "user_position": "petitioner",
        "opposing_party": "",
        "relevant_dates": relevant_dates,
        "selected_doc_ids": [],
        "case_overview": {},
        "fact_sheet": [],
        "evidence_findings": [],
        "arguments": [],
        "opposition": [],
        "risks": [],
        "precedents": [],
        "report": {},
    }
    return create_session(session_data)


@router.get("", response_model=List[WarRoomSessionResponse])
def get_war_room_sessions(user_id: Optional[str] = Depends(get_optional_user_id)):
    """Lists all active War Room sessions for the user."""
    return list_sessions(user_id=user_id)


@router.get("/{session_id}", response_model=WarRoomSessionResponse)
def get_single_war_room_session(session_id: str):
    """Retrieves full state of a single War Room session."""
    session = get_session_by_id(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"War Room session '{session_id}' not found.")
    return session


@router.patch("/{session_id}", response_model=WarRoomSessionResponse)
def update_war_room_session(session_id: str, payload: WarRoomSessionUpdate):
    """Updates editable case facts, positions, documents, or analyses."""
    raw_dict = payload.model_dump(exclude_unset=True) if hasattr(payload, "model_dump") else payload.dict(exclude_unset=True)
    updates = {k: v for k, v in raw_dict.items() if v is not None}
    if not updates:
        session = get_session_by_id(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"War Room session '{session_id}' not found.")
        return session

    updated = update_session(session_id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail=f"War Room session '{session_id}' not found.")
    return updated


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_war_room_session(session_id: str):
    """Permanently deletes a War Room session and its cache."""
    success = delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"War Room session '{session_id}' not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── Analysis Operations ───────────────────────────────────────────────────────

@router.post("/{session_id}/analyze", response_model=WarRoomAnalyzeResponse)
def analyze_war_room(
    session_id: str,
    payload: WarRoomAnalyzeRequest,
    user_id: Optional[str] = Depends(get_optional_user_id),
):
    """
    Executes a progressive analysis operation:
    'facts' | 'evidence' | 'arguments' | 'opposition' | 'risks' | 'report'
    """
    try:
        response = execute_war_room_analysis(
            session_id=session_id,
            operation=payload.operation,
            target_id=payload.target_id,
            force_refresh=payload.force_refresh,
            custom_instructions=payload.custom_instructions,
            user_id=user_id,
            query_text=payload.query_text,
            page=payload.page or 1,
            page_size=payload.page_size or 5,
        )
        return response
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/{session_id}/usage")
def get_war_room_usage(session_id: str):
    """Returns token usage, cache hits, and performance statistics for this session."""
    session = get_session_by_id(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"War Room session '{session_id}' not found.")
    return get_session_usage_summary(session_id)


@router.post("/{session_id}/export")
def export_strategy_report(session_id: str, format: str = "markdown"):
    """Exports the generated strategy report as formatted Markdown or text."""
    session = get_session_by_id(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"War Room session '{session_id}' not found.")

    report = session.get("report") or {}
    if not report:
        raise HTTPException(status_code=400, detail="No strategy report has been generated yet for this session.")

    posture = report.get('parties_and_procedural_posture') or report.get('parties_and_issues', 'N/A')
    chronology = report.get('verified_factual_chronology') or report.get('factual_chronology', 'N/A')
    issues = report.get('issues_for_determination', 'N/A')
    evidence = report.get('evidence_matrix') or report.get('evidence_analysis', 'N/A')
    args_and_counters = report.get('arguments_and_counterarguments') or f"### Affirmative Arguments:\n{report.get('affirmative_arguments', 'N/A')}\n\n### Opposition Stress-Test:\n{report.get('opposition_stress_test', 'N/A')}"
    precedents = report.get('precedent_landscape', 'N/A')
    risks_and_questions = report.get('risks_evidentiary_gaps_questions') or f"{report.get('risks_and_weaknesses', 'N/A')}\n\n### Unresolved Inquiries:\n{report.get('unresolved_questions', 'N/A')}"
    next_steps = report.get('practical_next_steps') or report.get('action_plan', 'N/A')
    limitations = report.get('limitations_and_verification_warnings', 'All cited authorities verified against official court records. Procedural stage strictly aligned.')

    md_content = f"""# 🏛️ NyayaSarathi Legal Strategy Report
**Case**: {session.get('title')}
**Forum**: {session.get('court')} ({session.get('jurisdiction')})
**Procedural Standing**: {session.get('user_position', 'appellant').upper()}
**Generated**: {report.get('generated_at', 'Recent')}

---

## 1. Executive Summary
{report.get('executive_summary', 'N/A')}

## 2. Parties, Selected Role, Forum & Procedural Posture
{posture}

## 3. Verified Factual Chronology
{chronology}

## 4. Issues for Determination
{issues}

## 5. Evidence Matrix & Source References
{evidence}

## 6. Arguments & Counterarguments
{args_and_counters}

## 7. Relevant Verified Judicial Precedents
{precedents}

## 8. Risks, Evidentiary Gaps & Unresolved Questions
{risks_and_questions}

## 9. Practical Next Steps (Stage-Appropriate)
{next_steps}

## 10. Limitations & Verification Warnings
{limitations}

---
*Disclaimer: {report.get('disclaimer')}*
"""

    return Response(
        content=md_content,
        media_type="text/markdown",
        headers={
            "Content-Disposition": f'attachment; filename="strategy_report_{session_id[:8]}.md"'
        },
    )


# ── Legacy Backward Compatibility ─────────────────────────────────────────────

@router.post("/simulate", response_model=WarRoomResponse)
def war_room_simulate(request: WarRoomRequest):
    """Simulate adversarial opposition arguments against a given legal position (legacy)."""
    return simulate_war_room(request)
