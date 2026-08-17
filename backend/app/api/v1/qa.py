from fastapi import APIRouter
from app.schemas.qa import QARequest, QAResponse
from app.services.qa_service import answer_question

router = APIRouter()

@router.post("/ask", response_model=QAResponse)
def ask_question(request: QARequest):
    """Ask a legal research question. Returns a grounded answer with exact-paragraph citations."""
    return answer_question(request)
