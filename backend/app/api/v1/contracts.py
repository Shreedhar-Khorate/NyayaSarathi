from fastapi import APIRouter, UploadFile, File
from app.schemas.contracts import ContractAnalysisResponse
from app.services.contracts_service import analyze_contract

router = APIRouter()

@router.post("/analyze", response_model=ContractAnalysisResponse)
async def analyze_contract_file(file: UploadFile = File(...)):
    """Upload a contract PDF/DOCX and receive a red-flag risk analysis."""
    # TODO: pass file bytes to a real OCR + NLP pipeline
    return analyze_contract(filename=file.filename or "uploaded_contract")
