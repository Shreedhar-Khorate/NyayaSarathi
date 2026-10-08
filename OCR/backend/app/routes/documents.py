import os
import uuid
import shutil
import time
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.schemas.document import DocumentResponse
from app.services.validator import validate_file
from app.services.document_processor import DocumentProcessor

logger = logging.getLogger("ocr_route")
router = APIRouter(prefix="/documents", tags=["documents"])

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(file: UploadFile = File(...)):
    start_time = time.time()
    logger.info(f"Document received: {file.filename}")
    
    await validate_file(file)
    logger.info("File validation passed")
    
    document_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{document_id}_{file.filename}")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    result = DocumentProcessor.process_digital(file_path, file.filename)
    
    duration = time.time() - start_time
    logger.info(f"Document processing completed in {duration:.2f} seconds")
        
    return DocumentResponse(
        document_id=document_id,
        filename=file.filename,
        status="completed",
        document_type=result["document_type"],
        pages=result["pages"],
        extraction_method=result["extraction_method"],
        text=result["text"],
        pages_data=result["pages_data"]
    )
