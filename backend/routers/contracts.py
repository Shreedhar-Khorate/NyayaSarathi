"""
NyayaSarathi Contracts Router — Contract Red-Flag Analysis API
Endpoint:
  - POST /api/contracts/analyze -> Upload PDF/DOCX contract and return structured risk analysis
"""

import os
from typing import Optional, Dict, Any
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status

from logger import get_logger
from schemas.contracts import ContractAnalysisResponse
from services.contracts_service import analyze_contract, MAX_FILE_SIZE_BYTES
from services.auth_dependencies import get_current_user

log = get_logger("nyayasarathi.contracts_router")

router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "application/octet-stream",  # Fallback for some browsers with docx/pdf
}


@router.post("/analyze", response_model=ContractAnalysisResponse, summary="Analyze Contract for Legal Risks")
async def analyze_contract_file(
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> ContractAnalysisResponse:
    """
    Accepts a legal contract (PDF, DOCX, TXT).
    1. Authenticates caller and enforces authorization.
    2. Validates format, MIME type, and size limits.
    3. Reliably extracts text (digital PDF, scanned OCR via PaddleOCR, or DOCX).
    4. Evaluates contract clauses using multi-provider AI and Indian legal risk rules.
    5. Returns categorized red flags, overall risk score, and source-grounded excerpts.
    """
    filename = file.filename or "uploaded_contract"
    ext = os.path.splitext(filename)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file format '{ext}'. Upload a PDF, DOCX, or TXT contract.",
        )

    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported content type '{file.content_type}'. Upload a PDF, DOCX, or TXT file.",
        )

    # Read bytes safely
    try:
        contents: bytes = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded file: {str(e)}",
        )

    if not contents or len(contents) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    if len(contents) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds the {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB limit.",
        )

    try:
        response = analyze_contract(
            filename=filename,
            content_type=file.content_type or "",
            file_bytes=contents,
        )

        # Log activity for authenticated user
        if current_user and current_user.get("id"):
            try:
                from services.user_repository import create_activity
                if response.audit_status == "COMPLETED":
                    activity_title = f"Analyzed Contract: {filename[:50]}"
                    query_summary = f"Contract Risk Analysis: {response.overall_risk_score} Risk ({len(response.red_flags)} red flags)"
                elif response.audit_status == "DOCUMENT_TYPE_MISMATCH":
                    activity_title = f"Document Mismatch: {filename[:50]}"
                    query_summary = f"Classified as {response.document_type_label} (Not a Contract - Audit Not Assessed)"
                else:
                    activity_title = f"Contract Audit ({response.audit_status}): {filename[:50]}"
                    query_summary = f"Status: {response.audit_status} ({response.classification_reason or 'Analysis Incomplete'})"

                create_activity(
                    user_id=current_user["id"],
                    activity_type="CONTRACT_ANALYSIS",
                    title=activity_title,
                    query_text=query_summary,
                    metadata={
                        "filename": filename,
                        "overall_risk_score": response.overall_risk_score,
                        "red_flags_count": len(response.red_flags),
                        "audit_status": response.audit_status,
                        "document_type": response.document_type,
                    },
                )
            except Exception as act_err:
                log.debug(f"Could not record user activity: {act_err}")

        return response

    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        )
    except HTTPException:
        raise
    except Exception as exc:
        log.error(f"Unexpected contract analysis error: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Contract analysis failed. Please verify the document format and try again.",
        )
