"""
FastAPI Router for AI Legal Translation Endpoint
Exposes POST /api/translate
"""
from fastapi import APIRouter, HTTPException
from schemas.translate import TranslationRequest, TranslationResponse
from services.translate_service import translate_legal_text

router = APIRouter()

@router.post("", response_model=TranslationResponse, summary="Translate Legal Text")
def translate(request: TranslationRequest) -> TranslationResponse:
    """
    Translates legal narrative text into target Indian regional languages (hi, mr, ta, gu, etc.)
    while preserving standard legal citation formatting and statutory references.
    """
    try:
        return translate_legal_text(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")
