"""
NyayaSarathi Legal Document OCR & Text Extraction Router.
Endpoints:
  - POST /api/ocr/process  -> Upload document (PDF/DOCX/image), detect type, run OCR, return unified extraction
  - POST /api/ocr/upload   -> Backward-compatible upload alias
"""

import os
import uuid
import time
import shutil
import logging
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Header, status
from schemas.ocr import OCRDocumentResponse, SendToResearchRequest
from schemas.qa import DocumentMetadata
from services.ocr.validator import validate_file
from services.ocr.ocr_processor import LegalOCRProcessor
from services.document_processor import get_document_processor
from services.auth_service import decode_access_token

logger = logging.getLogger("nyayasarathi.routers.ocr")

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "data", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_optional_user_id(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """Extracts user ID from Authorization header if present, else returns None."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ")[1]
    try:
        payload = decode_access_token(token)
        return payload.get("sub")
    except Exception:
        return None


@router.post("/process", response_model=OCRDocumentResponse, summary="Extract Text from Legal Document")
@router.post("/upload", response_model=OCRDocumentResponse, include_in_schema=False)
async def process_document(file: UploadFile = File(...)) -> OCRDocumentResponse:
    """
    Accepts a legal document (PDF, DOCX, JPG, PNG).
    1. Validates format and size limits.
    2. Detects digital text vs scanned imagery.
    3. Runs direct extraction for digital pages or OpenCV + PaddleOCR for scanned pages.
    4. Reconstructs natural reading order and extracts bounding boxes.
    5. Returns a unified structured response.
    """
    start_time = time.time()
    logger.info(f"Received document for OCR processing: {file.filename}")

    await validate_file(file)

    document_id = str(uuid.uuid4())
    safe_filename = os.path.basename(file.filename or "uploaded_document")
    file_path = os.path.join(UPLOAD_DIR, f"{document_id}_{safe_filename}")

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        result = LegalOCRProcessor.process_document(file_path, safe_filename)

        duration = time.time() - start_time
        logger.info(
            f"OCR processing completed in {duration:.2f}s for {safe_filename} "
            f"({result.get('pages', 0)} pages, method: {result.get('extraction_method')})"
        )

        return OCRDocumentResponse(
            document_id=document_id,
            filename=safe_filename,
            status="completed",
            document_type=result.get("document_type"),
            pages=result.get("pages"),
            extraction_method=result.get("extraction_method"),
            text=result.get("text"),
            pages_data=result.get("pages_data", [])
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process document {safe_filename}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OCR document processing failed: {str(e)}"
        )
    finally:
        # Keep uploaded file or clean up if needed
        pass


@router.post(
    "/send-to-research",
    response_model=DocumentMetadata,
    status_code=status.HTTP_201_CREATED,
    summary="Directly Ingest OCR Document into Legal Research / RAG",
)
async def send_to_research(
    request: SendToResearchRequest,
    user_id: Optional[str] = Depends(get_optional_user_id),
) -> DocumentMetadata:
    """
    Directly hands off a successfully extracted OCR document into the existing
    Legal Research knowledge base. Ingests, chunks, and indexes the document without
    requiring a second file upload or re-running OCR.
    """
    if not request.text or not request.text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot send empty document text to Legal Research.",
        )

    logger.info(f"Handoff OCR document to Legal Research: {request.filename} (ID: {request.document_id})")

    try:
        processor = get_document_processor()
        ocr_dict = request.model_dump() if hasattr(request, "model_dump") else request.dict()
        doc_info = processor.process_ocr_document(
            ocr_data=ocr_dict,
            user_id=user_id,
            custom_title=request.title,
        )

        return DocumentMetadata(
            id=doc_info["document_id"],
            title=doc_info["title"],
            filename=doc_info["filename"],
            file_type=doc_info["file_type"],
            file_size=doc_info["file_size"],
            total_pages=doc_info["total_pages"],
            total_chunks=doc_info["total_chunks"],
            status=doc_info["status"],
            created_at=doc_info["created_at"],
            user_id=user_id,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to ingest OCR document {request.document_id} into Legal Research: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send document to Legal Research: {str(e)}",
        )

