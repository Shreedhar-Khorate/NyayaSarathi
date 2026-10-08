"""
Upload Validator for Legal Document Extraction.
Validates file extension, MIME type, and size limits.
"""

import os
from fastapi import UploadFile, HTTPException

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".jpg", ".jpeg", ".png"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "image/jpeg",
    "image/png"
}


def get_max_file_size() -> int:
    return int(os.getenv("MAX_FILE_SIZE_MB", "50")) * 1024 * 1024


async def validate_file(file: UploadFile) -> bool:
    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported file format")

    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file format")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    if len(content) > get_max_file_size():
        raise HTTPException(status_code=400, detail="File exceeds maximum allowed size")

    await file.seek(0)
    return True


__all__ = ["validate_file", "ALLOWED_EXTENSIONS", "ALLOWED_MIME_TYPES"]
