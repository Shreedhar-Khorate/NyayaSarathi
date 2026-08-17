from fastapi import APIRouter
from app.schemas.drafts import DraftRequest, DraftResponse
from app.services.drafts_service import generate_draft

router = APIRouter()

@router.post("/generate", response_model=DraftResponse)
def generate_legal_draft(request: DraftRequest):
    """Generate a first-draft legal document with optional regional language translation."""
    return generate_draft(request)
