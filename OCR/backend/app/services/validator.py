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

def get_max_file_size():
    return int(os.getenv("MAX_FILE_SIZE_MB", "50")) * 1024 * 1024

async def validate_file(file: UploadFile):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported file format")
    
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file format")
        
    content = await file.read()
    if len(content) > get_max_file_size():
        raise HTTPException(status_code=400, detail="File exceeds maximum allowed size")
        
    await file.seek(0)
    return True
