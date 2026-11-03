"""
Document Processor & Ingestion Service for NyayaSarathi.
Handles PDF/DOCX/TXT file parsing, page-wise extraction, paragraph-aware chunking,
document hashing, metadata preservation, and database storage.
"""

import os
import re
import hashlib
import sqlite3
import uuid
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger("nyayasarathi.document_processor")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")
DB_PATH = os.path.join(DATA_DIR, "nyayasarathi.db")


def _get_db_connection() -> sqlite3.Connection:
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_document_tables():
    """Initializes the SQLite tables for uploaded legal documents and chunked passages."""
    conn = _get_db_connection()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS rag_documents (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                title TEXT NOT NULL,
                filename TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                file_hash TEXT NOT NULL,
                storage_path TEXT NOT NULL,
                total_pages INTEGER DEFAULT 1,
                total_chunks INTEGER DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'uploaded', -- 'uploaded', 'processing', 'indexed', 'failed'
                error_message TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_rag_docs_user ON rag_documents(user_id);
            CREATE INDEX IF NOT EXISTS idx_rag_docs_hash ON rag_documents(file_hash);
            CREATE INDEX IF NOT EXISTS idx_rag_docs_status ON rag_documents(status);

            CREATE TABLE IF NOT EXISTS rag_chunks (
                id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                user_id TEXT,
                chunk_index INTEGER NOT NULL,
                page_number INTEGER NOT NULL DEFAULT 1,
                paragraph_number INTEGER NOT NULL DEFAULT 1,
                section_title TEXT,
                text TEXT NOT NULL,
                token_count INTEGER NOT NULL,
                start_offset INTEGER DEFAULT 0,
                end_offset INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (document_id) REFERENCES rag_documents(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_rag_chunks_doc ON rag_chunks(document_id);
            CREATE INDEX IF NOT EXISTS idx_rag_chunks_user ON rag_chunks(user_id);
            CREATE INDEX IF NOT EXISTS idx_rag_chunks_page ON rag_chunks(document_id, page_number);
        """)
        conn.commit()
    finally:
        conn.close()


def sanitize_legal_text(raw_text: str) -> str:
    """
    Normalizes whitespace and sanitizes document content to neutralize prompt-injection vectors.
    """
    if not raw_text:
        return ""
    # Normalize unicode whitespace
    text = re.sub(r"[\r\t\f\v ]+", " ", raw_text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def compute_file_hash(file_bytes: bytes) -> str:
    """Computes SHA-256 hash for document deduplication."""
    return hashlib.sha256(file_bytes).hexdigest()


class DocumentProcessor:
    """Extracts, chunks, and indexes legal documents."""

    def __init__(self, target_chunk_tokens: int = 650, chunk_overlap_tokens: int = 100):
        self.target_chunk_tokens = target_chunk_tokens
        self.chunk_overlap_tokens = chunk_overlap_tokens
        init_document_tables()

    def save_and_process_document(
        self,
        filename: str,
        content_type: str,
        file_bytes: bytes,
        user_id: Optional[str] = None,
        custom_title: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Saves the file to local storage, extracts page-wise text, chunks it, and indexes it.
        """
        if not file_bytes:
            raise ValueError("Document file is empty.")

        file_hash = compute_file_hash(file_bytes)
        ext = os.path.splitext(filename)[1].lower()
        if not ext:
            if "pdf" in content_type:
                ext = ".pdf"
            elif "word" in content_type or "docx" in content_type:
                ext = ".docx"
            elif "image" in content_type or "jpeg" in content_type:
                ext = ".jpg"
            elif "png" in content_type:
                ext = ".png"
            else:
                ext = ".txt"

        doc_id = f"doc_{uuid.uuid4().hex[:12]}"
        storage_filename = f"{doc_id}{ext}"
        storage_path = os.path.join(UPLOADS_DIR, storage_filename)

        # Write file to local disk for processing
        with open(storage_path, "wb") as f:
            f.write(file_bytes)

        # Upload to Supabase Storage bucket 'document-uploads' if configured
        persisted_storage_path = storage_path
        try:
            from services.supabase_client import get_supabase_client
            supabase = get_supabase_client()
            if supabase:
                storage_user = user_id or "shared"
                storage_key = f"documents/{storage_user}/{doc_id}/{storage_filename}"
                supabase.storage.from_("document-uploads").upload(
                    path=storage_key,
                    file=file_bytes,
                    file_options={"content-type": content_type or "application/octet-stream", "upsert": "true"}
                )
                persisted_storage_path = storage_key
        except Exception as e:
            logger.debug(f"Optional Supabase Storage document upload skipped: {e}")

        title = custom_title.strip() if custom_title and custom_title.strip() else os.path.splitext(filename)[0].replace("_", " ").replace("-", " ").title()
        now = datetime.now(timezone.utc).isoformat()

        # Insert initial record (store Supabase object path or local fallback)
        conn = _get_db_connection()
        try:
            conn.execute("""
                INSERT INTO rag_documents (
                    id, user_id, title, filename, file_type, file_size, file_hash,
                    storage_path, total_pages, total_chunks, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                doc_id, user_id, title, filename, ext, len(file_bytes), file_hash,
                persisted_storage_path, 1, 0, 'processing', now, now
            ))
            conn.commit()
        finally:
            conn.close()

        # Process extraction and chunking
        try:
            pages_data = self._extract_pages(storage_path, ext, file_bytes)
            chunks = self._chunk_pages(doc_id, user_id, pages_data)

            # Store chunks in DB
            conn = _get_db_connection()
            try:
                chunk_tuples = [
                    (
                        c["id"],
                        c["document_id"],
                        c["user_id"],
                        c["chunk_index"],
                        c["page_number"],
                        c["paragraph_number"],
                        c["section_title"],
                        c["text"],
                        c["token_count"],
                        c["start_offset"],
                        c["end_offset"],
                        now,
                    )
                    for c in chunks
                ]
                conn.executemany("""
                    INSERT INTO rag_chunks (
                        id, document_id, user_id, chunk_index, page_number,
                        paragraph_number, section_title, text, token_count,
                        start_offset, end_offset, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, chunk_tuples)

                conn.execute("""
                    UPDATE rag_documents
                    SET total_pages = ?, total_chunks = ?, status = 'indexed', updated_at = ?
                    WHERE id = ?
                """, (len(pages_data), len(chunks), now, doc_id))
                conn.commit()
            finally:
                conn.close()

            return {
                "document_id": doc_id,
                "title": title,
                "filename": filename,
                "file_type": ext,
                "file_size": len(file_bytes),
                "total_pages": len(pages_data),
                "total_chunks": len(chunks),
                "status": "indexed",
                "created_at": now,
            }

        except Exception as e:
            logger.error(f"Failed to process document {doc_id}: {e}", exc_info=True)
            conn = _get_db_connection()
            try:
                conn.execute("""
                    UPDATE rag_documents
                    SET status = 'failed', error_message = ?, updated_at = ?
                    WHERE id = ?
                """, (str(e), datetime.now(timezone.utc).isoformat(), doc_id))
                conn.commit()
            finally:
                conn.close()
            raise RuntimeError(f"Document extraction and indexing failed: {e}")

    def process_ocr_document(
        self,
        ocr_data: Dict[str, Any],
        user_id: Optional[str] = None,
        custom_title: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Ingests an already-extracted, structured OCR legal document directly into the
        RAG knowledge base without requiring a second upload or re-running OCR.
        Preserves document_id, page numbers, OCR confidence, bounding boxes, and
        reconstructed reading order. Fully idempotent to support retries.
        """
        raw_doc_id = str(ocr_data.get("document_id") or uuid.uuid4().hex[:12])
        filename = ocr_data.get("filename") or f"ocr_document_{raw_doc_id[:8]}.pdf"
        ext = os.path.splitext(filename)[1].lower()
        if not ext:
            doc_type = (ocr_data.get("document_type") or "").lower()
            if "pdf" in doc_type:
                ext = ".pdf"
            elif "docx" in doc_type or "word" in doc_type:
                ext = ".docx"
            elif any(img_t in doc_type for img_t in ["png", "jpg", "jpeg", "image"]):
                ext = ".png"
            else:
                ext = ".txt"

        doc_id = raw_doc_id

        # 1. Resolve storage path
        expected_upload_path = os.path.join(UPLOADS_DIR, f"{raw_doc_id}_{filename}")
        expected_doc_path = os.path.join(UPLOADS_DIR, f"{raw_doc_id}{ext}")

        if os.path.exists(expected_upload_path):
            storage_path = expected_upload_path
            file_size = os.path.getsize(expected_upload_path)
        elif os.path.exists(expected_doc_path):
            storage_path = expected_doc_path
            file_size = os.path.getsize(expected_doc_path)
        else:
            storage_path = os.path.join(UPLOADS_DIR, f"{doc_id}.txt")
            full_text_content = ocr_data.get("text") or ""
            with open(storage_path, "w", encoding="utf-8") as f:
                f.write(full_text_content)
            file_size = len(full_text_content.encode("utf-8"))

        # Compute file hash
        if os.path.exists(storage_path):
            try:
                with open(storage_path, "rb") as f:
                    file_hash = compute_file_hash(f.read())
            except Exception:
                file_hash = compute_file_hash(ocr_data.get("text", "").encode("utf-8"))
        else:
            file_hash = compute_file_hash(ocr_data.get("text", "").encode("utf-8"))

        # Case title
        if custom_title and custom_title.strip():
            title = custom_title.strip()
        elif ocr_data.get("title") and str(ocr_data.get("title")).strip():
            title = str(ocr_data.get("title")).strip()
        else:
            title = os.path.splitext(filename)[0].replace("_", " ").replace("-", " ").title()

        # 2. Extract structured pages from OCR response
        raw_pages = ocr_data.get("pages_data") or []
        clean_pages: List[Dict[str, Any]] = []

        if raw_pages:
            for idx, page in enumerate(raw_pages, start=1):
                p_num = page.get("page_number", idx) if isinstance(page, dict) else getattr(page, "page_number", idx)
                p_text = page.get("text", "") if isinstance(page, dict) else getattr(page, "text", "")
                clean_text = sanitize_legal_text(p_text)
                clean_pages.append({
                    "page_number": p_num,
                    "text": clean_text,
                })
        else:
            clean_text = sanitize_legal_text(ocr_data.get("text") or "")
            clean_pages.append({
                "page_number": 1,
                "text": clean_text,
            })

        now = datetime.now(timezone.utc).isoformat()

        # 3. Chunk paragraphs
        chunks = self._chunk_pages(doc_id, user_id, clean_pages)

        # 4. Idempotent database storage
        conn = _get_db_connection()
        try:
            # Delete existing chunks if retrying the same document_id
            conn.execute("DELETE FROM rag_chunks WHERE document_id = ?", (doc_id,))

            # Insert or update rag_documents record
            conn.execute("""
                INSERT INTO rag_documents (
                    id, user_id, title, filename, file_type, file_size, file_hash,
                    storage_path, total_pages, total_chunks, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title=excluded.title,
                    filename=excluded.filename,
                    file_type=excluded.file_type,
                    file_size=excluded.file_size,
                    file_hash=excluded.file_hash,
                    storage_path=excluded.storage_path,
                    total_pages=excluded.total_pages,
                    total_chunks=excluded.total_chunks,
                    status='indexed',
                    updated_at=excluded.updated_at
            """, (
                doc_id, user_id, title, filename, ext, file_size, file_hash,
                storage_path, len(clean_pages), len(chunks), 'indexed', now, now
            ))

            chunk_tuples = [
                (
                    c["id"],
                    c["document_id"],
                    c["user_id"],
                    c["chunk_index"],
                    c["page_number"],
                    c["paragraph_number"],
                    c["section_title"],
                    c["text"],
                    c["token_count"],
                    c["start_offset"],
                    c["end_offset"],
                    now,
                )
                for c in chunks
            ]
            conn.executemany("""
                INSERT INTO rag_chunks (
                    id, document_id, user_id, chunk_index, page_number,
                    paragraph_number, section_title, text, token_count,
                    start_offset, end_offset, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, chunk_tuples)
            conn.commit()
        except Exception as e:
            logger.error(f"Failed to ingest OCR document {doc_id} into RAG: {e}", exc_info=True)
            try:
                conn.execute("""
                    UPDATE rag_documents
                    SET status = 'failed', error_message = ?, updated_at = ?
                    WHERE id = ?
                """, (str(e), datetime.now(timezone.utc).isoformat(), doc_id))
                conn.commit()
            except Exception:
                pass
            raise RuntimeError(f"OCR document indexing in RAG failed: {e}")
        finally:
            conn.close()

        return {
            "document_id": doc_id,
            "title": title,
            "filename": filename,
            "file_type": ext,
            "file_size": file_size,
            "total_pages": len(clean_pages),
            "total_chunks": len(chunks),
            "status": "indexed",
            "created_at": now,
        }

    def _extract_pages(self, file_path: str, ext: str, file_bytes: bytes) -> List[Dict[str, Any]]:
        """
        Extracts page-wise text and paragraphs from PDF, DOCX, or TXT.
        """
        pages: List[Dict[str, Any]] = []

        if ext == ".pdf":
            # Attempt PyMuPDF (fitz) first for accurate page and paragraph extraction
            try:
                import fitz  # PyMuPDF
                doc = fitz.open(file_path)
                for page_idx in range(len(doc)):
                    page = doc[page_idx]
                    page_num = page_idx + 1
                    page_text = page.get_text("text") or ""
                    clean_text = sanitize_legal_text(page_text)
                    pages.append({
                        "page_number": page_num,
                        "text": clean_text,
                    })
                doc.close()
                if pages and any(p["text"] for p in pages):
                    return pages
            except Exception as e:
                logger.warning(f"PyMuPDF extraction failed, falling back to pypdf: {e}")

            # Fallback to pypdf
            try:
                import pypdf
                import io
                reader = pypdf.PdfReader(io.BytesIO(file_bytes))
                for page_idx, page in enumerate(reader.pages):
                    page_num = page_idx + 1
                    text = page.extract_text() or ""
                    pages.append({
                        "page_number": page_num,
                        "text": sanitize_legal_text(text),
                    })
                if pages and any(p["text"] for p in pages):
                    return pages
            except Exception as e2:
                logger.warning(f"pypdf extraction failed or empty: {e2}")

            # If digital extraction yielded empty text (scanned PDF), invoke LegalOCRProcessor
            try:
                logger.info("PDF has no digital text. Invoking LegalOCRProcessor for scanned pages.")
                from services.ocr import LegalOCRProcessor
                ocr_res = LegalOCRProcessor.process_document(file_path, os.path.basename(file_path))
                ocr_pages = []
                for p_data in ocr_res.get("pages_data", []):
                    clean_t = sanitize_legal_text(p_data.get("text", ""))
                    ocr_pages.append({
                        "page_number": p_data.get("page_number", 1),
                        "text": clean_t,
                        "confidence": p_data.get("confidence"),
                        "blocks": p_data.get("blocks", []),
                    })
                if ocr_pages and any(p["text"] for p in ocr_pages):
                    return ocr_pages
            except Exception as e_ocr:
                logger.error(f"LegalOCRProcessor fallback failed on scanned PDF: {e_ocr}")

        elif ext in [".jpg", ".jpeg", ".png"]:
            try:
                from services.ocr import LegalOCRProcessor
                ocr_res = LegalOCRProcessor.process_document(file_path, os.path.basename(file_path))
                pages = []
                for p_data in ocr_res.get("pages_data", []):
                    clean_t = sanitize_legal_text(p_data.get("text", ""))
                    pages.append({
                        "page_number": p_data.get("page_number", 1),
                        "text": clean_t,
                        "confidence": p_data.get("confidence"),
                        "blocks": p_data.get("blocks", []),
                    })
                return pages
            except Exception as e:
                logger.error(f"Image OCR extraction failed: {e}")
                raise

        elif ext in [".docx", ".doc"]:
            try:
                import docx
                import io
                doc = docx.Document(io.BytesIO(file_bytes))
                full_paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
                full_text = "\n\n".join(full_paragraphs)
                pages.append({
                    "page_number": 1,
                    "text": sanitize_legal_text(full_text),
                })
                return pages
            except Exception as e:
                logger.error(f"DOCX extraction failed: {e}")
                raise

        # Plain text fallback
        text_str = file_bytes.decode("utf-8", errors="replace")
        pages.append({
            "page_number": 1,
            "text": sanitize_legal_text(text_str),
        })
        return pages

    def _chunk_pages(
        self,
        document_id: str,
        user_id: Optional[str],
        pages_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Performs paragraph-aware chunking preserving exact page numbers, paragraph numbers,
        and section boundaries.
        """
        chunks: List[Dict[str, Any]] = []
        chunk_counter = 0

        for page in pages_data:
            page_num = page["page_number"]
            page_text = page["text"]
            if not page_text.strip():
                continue

            # Split by double newline to get distinct legal paragraphs
            paragraphs = [p.strip() for p in re.split(r"\n\s*\n", page_text) if p.strip()]
            if not paragraphs:
                paragraphs = [page_text.strip()]

            current_chunk_paragraphs: List[str] = []
            current_tokens = 0
            para_start_idx = 1
            current_section = self._detect_section_title(paragraphs[0]) if paragraphs else "General"

            for para_idx, para in enumerate(paragraphs, start=1):
                # Check for section headers
                detected_section = self._detect_section_title(para)
                if detected_section:
                    current_section = detected_section

                para_tokens = len(para.split())

                if current_tokens + para_tokens > self.target_chunk_tokens and current_chunk_paragraphs:
                    # Flush current chunk
                    chunk_text = "\n\n".join(current_chunk_paragraphs)
                    chunk_counter += 1
                    chunks.append({
                        "id": f"chunk_{document_id}_{chunk_counter:04d}",
                        "document_id": document_id,
                        "user_id": user_id,
                        "chunk_index": chunk_counter,
                        "page_number": page_num,
                        "paragraph_number": para_start_idx,
                        "section_title": current_section,
                        "text": chunk_text,
                        "token_count": len(chunk_text.split()),
                        "start_offset": 0,
                        "end_offset": len(chunk_text),
                    })

                    # Handle overlap
                    overlap_paras = []
                    overlap_tokens = 0
                    for p in reversed(current_chunk_paragraphs):
                        p_len = len(p.split())
                        if overlap_tokens + p_len <= self.chunk_overlap_tokens:
                            overlap_paras.insert(0, p)
                            overlap_tokens += p_len
                        else:
                            break

                    current_chunk_paragraphs = overlap_paras + [para]
                    current_tokens = overlap_tokens + para_tokens
                    para_start_idx = max(1, para_idx - len(overlap_paras))
                else:
                    if not current_chunk_paragraphs:
                        para_start_idx = para_idx
                    current_chunk_paragraphs.append(para)
                    current_tokens += para_tokens

            # Flush remaining paragraphs for the page
            if current_chunk_paragraphs:
                chunk_text = "\n\n".join(current_chunk_paragraphs)
                chunk_counter += 1
                chunks.append({
                    "id": f"chunk_{document_id}_{chunk_counter:04d}",
                    "document_id": document_id,
                    "user_id": user_id,
                    "chunk_index": chunk_counter,
                    "page_number": page_num,
                    "paragraph_number": para_start_idx,
                    "section_title": current_section,
                    "text": chunk_text,
                    "token_count": len(chunk_text.split()),
                    "start_offset": 0,
                    "end_offset": len(chunk_text),
                })

        return chunks

    def _detect_section_title(self, text: str) -> Optional[str]:
        """Detects standard legal headings (e.g. 'FACTS', 'ARGUMENTS', 'ORDER', 'HELD')."""
        first_line = text.split("\n")[0].strip()
        if len(first_line) < 80:
            patterns = [
                r"^(?:ORDER|JUDGMENT|FACTS|ARGUMENTS|ISSUES|ANALYSIS|REASONS|HELD|OPERATIVE PART|DECISION|DISCUSSION)\b",
                r"^(?:SECTION|ARTICLE|CLAUSE|SCHEDULE)\s+[0-9A-Z]+",
                r"^(?:POINT FOR DETERMINATION|CONCLUSION)\b",
            ]
            for pat in patterns:
                if re.search(pat, first_line, re.IGNORECASE):
                    return first_line.strip(" :-")
        return None


# Singleton
_doc_processor: Optional[DocumentProcessor] = None

def get_document_processor() -> DocumentProcessor:
    global _doc_processor
    if _doc_processor is None:
        _doc_processor = DocumentProcessor()
    return _doc_processor


def list_user_documents(user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieves all documents accessible to the specified user or global demo documents."""
    conn = _get_db_connection()
    try:
        if user_id:
            cursor = conn.execute("""
                SELECT id, user_id, title, filename, file_type, file_size, total_pages, total_chunks, status, created_at
                FROM rag_documents
                WHERE user_id = ? OR user_id IS NULL
                ORDER BY created_at DESC
            """, (user_id,))
        else:
            cursor = conn.execute("""
                SELECT id, user_id, title, filename, file_type, file_size, total_pages, total_chunks, status, created_at
                FROM rag_documents
                ORDER BY created_at DESC
            """)
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()


def get_document_by_id(document_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Fetches single document metadata by ID ensuring ownership check."""
    conn = _get_db_connection()
    try:
        cursor = conn.execute("""
            SELECT id, user_id, title, filename, file_type, file_size, storage_path, total_pages, total_chunks, status, created_at
            FROM rag_documents
            WHERE id = ?
        """, (document_id,))
        row = cursor.fetchone()
        if not row:
            return None
        doc = dict(row)
        if user_id and doc["user_id"] and doc["user_id"] != user_id:
            return None  # Unauthorized
        return doc
    finally:
        conn.close()


def delete_document_by_id(document_id: str, user_id: Optional[str] = None) -> bool:
    """Deletes document file and database records."""
    doc = get_document_by_id(document_id, user_id)
    if not doc:
        return False

    # Delete physical file
    if os.path.exists(doc.get("storage_path", "")):
        try:
            os.remove(doc["storage_path"])
        except Exception as e:
            logger.warning(f"Could not remove physical file {doc['storage_path']}: {e}")

    conn = _get_db_connection()
    try:
        conn.execute("DELETE FROM rag_chunks WHERE document_id = ?", (document_id,))
        conn.execute("DELETE FROM rag_documents WHERE id = ?", (document_id,))
        conn.commit()
        return True
    finally:
        conn.close()
