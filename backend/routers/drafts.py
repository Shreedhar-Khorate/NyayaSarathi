"""
NyayaSarathi Legal Drafting Router — Feature 3.8
Provides endpoints for AI legal drafting, section regeneration,
regional Indic language translation, and PDF/DOCX document export.
"""

from fastapi import APIRouter, Response, Depends, status
from fastapi.responses import StreamingResponse
import io
import urllib.parse

from schemas.drafts import (
    DraftRequest,
    DraftResponse,
    DraftContent,
    RegenerateSectionRequest,
    RegenerateSectionResponse,
    TranslateDraftRequest,
    ExportDraftRequest,
)
from services.drafts_service import (
    generate_draft,
    regenerate_draft_section,
    translate_draft,
)
from services.draft_export import generate_draft_pdf, generate_draft_docx

router = APIRouter()


@router.post("/generate", response_model=DraftResponse, status_code=status.HTTP_200_OK)
def generate_legal_draft(request: DraftRequest):
    """
    Generate a structured, verified first-draft legal document (Legal Notice,
    Bail Application, Petition, Reply) grounded in case facts, statutory concordance,
    and optional regional Indic translation.
    """
    return generate_draft(request)


@router.post("/regenerate-section", response_model=RegenerateSectionResponse, status_code=status.HTTP_200_OK)
def regenerate_section(request: RegenerateSectionRequest):
    """
    Regenerate a designated section of a legal draft based on customized advocate
    instructions without modifying unrelated sections.
    """
    return regenerate_draft_section(request)


@router.post("/translate", response_model=DraftContent, status_code=status.HTTP_200_OK)
def translate_existing_draft(request: TranslateDraftRequest):
    """
    Translate an existing draft into a supported regional language ('hi', 'mr', 'en')
    with strict preservation of legal citations, placeholders, and party names.
    """
    return translate_draft(request)


@router.post("/export/pdf")
def export_draft_as_pdf(request: ExportDraftRequest):
    """
    Export the legal draft as a downloadable, professionally formatted court PDF
    with running headers, legal disclaimers, and citation appendices.
    """
    pdf_bytes = generate_draft_pdf(request)
    filename = f"{request.document_type.replace(' ', '_').lower()}_draft.pdf"
    encoded_filename = urllib.parse.quote(filename)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=\"{filename}\"; filename*=UTF-8''{encoded_filename}",
            "Content-Type": "application/pdf",
        },
    )


@router.post("/export/docx")
def export_draft_as_docx(request: ExportDraftRequest):
    """
    Export the legal draft as an editable DOCX Word document preserving heading
    hierarchy, paragraph indentation, disclaimers, and citation tables.
    """
    docx_bytes = generate_draft_docx(request)
    filename = f"{request.document_type.replace(' ', '_').lower()}_draft.docx"
    encoded_filename = urllib.parse.quote(filename)

    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f"attachment; filename=\"{filename}\"; filename*=UTF-8''{encoded_filename}",
            "Content-Type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        },
    )
