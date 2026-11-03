"""
NyayaSarathi RAG Legal Q&A Router.
Provides:
  - POST /api/qa/ask               -> Grounded Legal Q&A with verifiable citations
  - POST /api/qa/documents/upload  -> Ingest and index PDF, DOCX, or TXT
  - GET  /api/qa/documents         -> List accessible documents
  - GET  /api/qa/documents/{id}    -> Fetch document metadata & chunks
  - GET  /api/qa/documents/{id}/file -> Stream raw file for in-browser document viewer
  - DELETE /api/qa/documents/{id}  -> Delete document & indexed chunks
"""

import os
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Header, status
from fastapi.responses import FileResponse

from schemas.qa import (
    QARequest,
    QAResponse,
    DocumentMetadata,
    DocumentListResponse,
    DocumentDetailResponse,
    ChunkMetadata,
)
from schemas.ocr import SendToResearchRequest
from services.qa_service import answer_question
from services.document_processor import (
    get_document_processor,
    list_user_documents,
    get_document_by_id,
    delete_document_by_id,
    _get_db_connection,
)
from services.auth_service import decode_access_token

router = APIRouter()


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


@router.post("/ask", response_model=QAResponse)
def ask_question(
    request: QARequest,
    user_id: Optional[str] = Depends(get_optional_user_id),
):
    """
    Ask a legal research question scoped to selected documents.
    Returns an evidence-grounded answer with verified [S1], [S2] source citations.
    """
    if not request.question or len(request.question.strip()) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question must be at least 3 characters long.",
        )
    res = answer_question(request, user_id=user_id)
    if user_id:
        try:
            from services.user_repository import create_activity
            create_activity(
                user_id=user_id,
                activity_type="LEGAL_RESEARCH",
                title=f"Research: {request.question[:60]}...",
                query_text=request.question,
                metadata={"doc_ids": request.document_ids or []},
            )
        except Exception:
            pass
    return res


@router.post("/documents/upload", response_model=DocumentMetadata, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    user_id: Optional[str] = Depends(get_optional_user_id),
):
    """
    Upload a legal document (PDF, DOCX, TXT), extract pages, chunk paragraphs,
    and index for hybrid retrieval.
    """
    allowed_extensions = {".pdf", ".docx", ".doc", ".txt"}
    filename = file.filename or "uploaded_document"
    ext = os.path.splitext(filename)[1].lower()

    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file format '{ext}'. Only PDF, DOCX, and TXT are supported.",
        )

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    # 30 MB file size limit
    if len(file_bytes) > 30 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds the 30 MB limit.",
        )

    processor = get_document_processor()
    try:
        doc_info = processor.save_and_process_document(
            filename=filename,
            content_type=file.content_type or "",
            file_bytes=file_bytes,
            user_id=user_id,
            custom_title=title,
        )
        meta = DocumentMetadata(
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
        if user_id:
            try:
                from services.user_repository import create_activity
                create_activity(
                    user_id=user_id,
                    activity_type="DOCUMENT_UPLOAD",
                    title=f"Uploaded: {doc_info['title']}",
                    resource_id=doc_info["document_id"],
                    metadata={"filename": doc_info["filename"], "file_type": doc_info["file_type"]},
                )
            except Exception:
                pass
        return meta
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document indexing failed: {str(e)}",
        )


@router.post("/documents/from-ocr", response_model=DocumentMetadata, status_code=status.HTTP_201_CREATED)
async def ingest_document_from_ocr(
    request: SendToResearchRequest,
    user_id: Optional[str] = Depends(get_optional_user_id),
):
    """
    Ingest a structured OCR result directly into the Legal Research knowledge base.
    Avoids requiring the user to re-upload the same document.
    """
    if not request.text or not request.text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot ingest empty document text into Legal Research.",
        )

    processor = get_document_processor()
    try:
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
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OCR handoff to Legal Research failed: {str(e)}",
        )


@router.get("/documents", response_model=DocumentListResponse)
def list_documents(user_id: Optional[str] = Depends(get_optional_user_id)):
    """List all documents available for research."""
    docs = list_user_documents(user_id)
    return DocumentListResponse(
        documents=[
            DocumentMetadata(
                id=d["id"],
                title=d["title"],
                filename=d["filename"],
                file_type=d["file_type"],
                file_size=d["file_size"],
                total_pages=d["total_pages"],
                total_chunks=d["total_chunks"],
                status=d["status"],
                created_at=d["created_at"],
                user_id=d.get("user_id"),
            )
            for d in docs
        ]
    )


@router.get("/documents/{document_id}", response_model=DocumentDetailResponse)
def get_document_details(
    document_id: str,
    user_id: Optional[str] = Depends(get_optional_user_id),
):
    """Retrieve metadata and indexed chunks for a single document."""
    doc = get_document_by_id(document_id, user_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found or access denied.",
        )

    conn = _get_db_connection()
    try:
        cursor = conn.execute("""
            SELECT id, chunk_index, page_number, paragraph_number, section_title, text, token_count
            FROM rag_chunks
            WHERE document_id = ?
            ORDER BY chunk_index ASC
        """, (document_id,))
        chunks = [
            ChunkMetadata(
                id=r["id"],
                chunk_index=r["chunk_index"],
                page_number=r["page_number"],
                paragraph_number=r["paragraph_number"],
                section_title=r["section_title"],
                text=r["text"],
                token_count=r["token_count"],
            )
            for r in cursor.fetchall()
        ]
    finally:
        conn.close()

    metadata = DocumentMetadata(
        id=doc["id"],
        title=doc["title"],
        filename=doc["filename"],
        file_type=doc["file_type"],
        file_size=doc["file_size"],
        total_pages=doc["total_pages"],
        total_chunks=doc["total_chunks"],
        status=doc["status"],
        created_at=doc["created_at"],
        user_id=doc.get("user_id"),
    )

    return DocumentDetailResponse(document=metadata, chunks=chunks)


@router.get("/documents/{document_id}/file")
def get_document_file(
    document_id: str,
    user_id: Optional[str] = Depends(get_optional_user_id),
):
    """
    Serves the raw document file for in-browser PDF / document rendering.
    Supports streaming from local disk or direct retrieval from Supabase Storage.
    """
    doc = get_document_by_id(document_id, user_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found.",
        )

    file_path = doc.get("storage_path")
    media_type = "application/pdf" if doc["file_type"] == ".pdf" else "application/octet-stream"

    # 1. Check local file system
    if file_path and os.path.exists(file_path):
        return FileResponse(
            path=file_path,
            media_type=media_type,
            filename=doc["filename"],
        )

    # 2. Check Supabase Storage if file_path is a storage object key or if local copy is missing
    from services.supabase_client import get_supabase_client
    supabase = get_supabase_client()
    if supabase and file_path:
        try:
            from fastapi.responses import Response
            bucket = "document-uploads"
            file_bytes = supabase.storage.from_(bucket).download(file_path)
            if file_bytes:
                return Response(
                    content=file_bytes,
                    media_type=media_type,
                    headers={"Content-Disposition": f'inline; filename="{doc["filename"]}"'},
                )
        except Exception:
            pass

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Physical file does not exist on storage.",
    )


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: str,
    user_id: Optional[str] = Depends(get_optional_user_id),
):
    """Deletes a document and all associated chunks."""
    success = delete_document_by_id(document_id, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found or access denied.",
        )
    return None
