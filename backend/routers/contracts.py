from fastapi import APIRouter, UploadFile, File, HTTPException
from schemas.contracts import ContractAnalysisResponse
from services.contracts_service import analyze_contract

router = APIRouter()


@router.post("/analyze", response_model=ContractAnalysisResponse)
async def analyze_contract_file(file: UploadFile = File(...)):
    """Upload a contract PDF/DOCX and receive a red-flag risk analysis."""
    allowed_types = {"application/pdf", "application/msword",
                     "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                     "text/plain"}

    if file.content_type and file.content_type not in allowed_types:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{file.content_type}'. Upload a PDF, DOCX, or TXT file."
        )

    # Read the actual file bytes
    contents: bytes = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    return analyze_contract(
        filename=file.filename or "uploaded_contract",
        content_type=file.content_type or "",
        file_bytes=contents,
    )
