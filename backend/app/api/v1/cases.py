from fastapi import APIRouter, HTTPException
from typing import List
from app.schemas.cases import Case, CreateCaseRequest, TimelineResponse
from app.services.cases_service import create_case, list_cases, get_case, get_timeline

router = APIRouter()

@router.get("", response_model=List[Case])
def get_all_cases():
    """List all active cases."""
    return list_cases()

@router.post("", response_model=Case, status_code=201)
def new_case(request: CreateCaseRequest):
    """Create a new case."""
    return create_case(request)

@router.get("/{case_id}", response_model=Case)
def get_one_case(case_id: str):
    """Get a single case by ID."""
    case = get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")
    return case

@router.get("/{case_id}/timeline", response_model=TimelineResponse)
def case_timeline(case_id: str):
    """Get the chronological event timeline for a case."""
    return get_timeline(case_id)
