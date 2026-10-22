"""
NyayaSarathi Pydantic Schemas for Legal Drafting, Regeneration, Translation, and Export.
Feature 3.8: Dynamic LLM Legal Drafting (Zero RAG, Zero Static Fallbacks).
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator


# ── Canonical Document Types & Supported Languages ────────────────────────────
SUPPORTED_DOCUMENT_TYPES = {
    "legal_notice",
    "bail_application",
    "regular_bail",
    "anticipatory_bail",
    "petition",
    "writ_petition",
    "slp",
    "quashing_petition",
    "reply",
    "written_statement",
    "counter_affidavit",
    "reply_to_notice",
}

CANONICAL_DOCUMENT_TYPE_MAP = {
    "legal_notice": ("legal_notice", "legal_notice"),
    "legal notice": ("legal_notice", "legal_notice"),
    "notice": ("legal_notice", "legal_notice"),
    "demand_notice": ("legal_notice", "demand_notice"),
    "demand notice": ("legal_notice", "demand_notice"),
    "statutory_notice": ("legal_notice", "statutory_notice"),
    "bail_application": ("bail_application", "regular_bail"),
    "bail application": ("bail_application", "regular_bail"),
    "bail": ("bail_application", "regular_bail"),
    "regular_bail": ("bail_application", "regular_bail"),
    "regular bail": ("bail_application", "regular_bail"),
    "anticipatory_bail": ("bail_application", "anticipatory_bail"),
    "anticipatory bail": ("bail_application", "anticipatory_bail"),
    "petition": ("petition", "general_petition"),
    "writ_petition": ("petition", "writ_petition"),
    "writ petition": ("petition", "writ_petition"),
    "slp": ("petition", "slp"),
    "special_leave_petition": ("petition", "slp"),
    "special leave petition": ("petition", "slp"),
    "quashing_petition": ("petition", "quashing_petition"),
    "quashing petition": ("petition", "quashing_petition"),
    "reply": ("reply", "reply_to_notice"),
    "reply_to_notice": ("reply", "reply_to_notice"),
    "reply to notice": ("reply", "reply_to_notice"),
    "reply to legal notice": ("reply", "reply_to_notice"),
    "written_statement": ("reply", "written_statement"),
    "written statement": ("reply", "written_statement"),
    "counter_affidavit": ("reply", "counter_affidavit"),
    "counter affidavit": ("reply", "counter_affidavit"),
}

SUPPORTED_LANGUAGES = {"en", "hi", "mr", "english", "hindi", "marathi"}


def resolve_canonical_doc_type(raw_type: Optional[str]) -> Optional[tuple[str, str]]:
    """Resolves raw document type string to (canonical_doc_type, subtype)."""
    if not raw_type or not str(raw_type).strip():
        return None
    clean = str(raw_type).strip().lower().replace("-", "_")
    if clean in CANONICAL_DOCUMENT_TYPE_MAP:
        return CANONICAL_DOCUMENT_TYPE_MAP[clean]
    clean_no_under = clean.replace("_", " ")
    if clean_no_under in CANONICAL_DOCUMENT_TYPE_MAP:
        return CANONICAL_DOCUMENT_TYPE_MAP[clean_no_under]
    return None


# ── Section Model ─────────────────────────────────────────────────────────────
class DraftSection(BaseModel):
    id: str = Field(..., description="Unique section identifier (e.g. 'sec_header', 'sec_grounds')")
    title: str = Field(..., description="Display title for the legal section")
    content: str = Field(..., description="The substantive drafted text of the section")
    order: int = Field(0, description="Sequential ordering index", ge=0)

    @field_validator("id", "title", "content")
    @classmethod
    def check_non_blank(cls, v: str, info) -> str:
        if not v or not str(v).strip():
            raise ValueError(f"DraftSection field '{info.field_name}' must not be empty or blank whitespace.")
        return str(v).strip()


# ── Citation Info Model ───────────────────────────────────────────────────────
class CitationInfo(BaseModel):
    source_id: Optional[str] = Field(None, description="Descriptive identifier for citation (not a fake retrieved evidence chunk ID)")
    title: str = Field(..., description="Name of the case, statutory act, or legal authority")
    citation: str = Field(..., description="Standard formal citation (e.g., Section 480 BNSS, 2023 or AIR 2024 SC 123)")
    court: Optional[str] = Field(None, description="Adjudicating court if applicable")
    decision_date: Optional[str] = Field(None, description="Date or year of judgment")
    source_url: Optional[str] = Field(None, description="Authentic repository URL or document locator if available")
    excerpt: Optional[str] = Field(None, description="Authoritative excerpt supporting the assertion; optional when not available from source")
    is_verified: bool = Field(False, description="Whether citation was independently verified against authentic source records; defaults to False")
    verification_status: str = Field("verification_required", description="'unverified', 'verification_required', 'user_supplied', or 'verified_primary_source'")
    authority_type: str = Field("statutory", description="'statutory', 'binding_precedent', 'persuasive_authority', 'unverified', or 'user_supplied_provision'")
    provenance: Optional[str] = Field(None, description="Provenance: 'user_supplied', 'llm_suggested', or 'verified_source'")
    relevant_statement: Optional[str] = Field(None, description="The legal statement or section supported by this citation")

    @field_validator("title", "citation")
    @classmethod
    def check_non_blank_cit(cls, v: str, info) -> str:
        if not v or not str(v).strip():
            raise ValueError(f"CitationInfo field '{info.field_name}' cannot be empty.")
        return str(v).strip()

    @field_validator("verification_status")
    @classmethod
    def validate_verification_status(cls, v: str) -> str:
        allowed = {"unverified", "verification_required", "user_supplied", "verified_primary_source", "VERIFIED"}
        clean = v.strip().lower()
        if clean not in [a.lower() for a in allowed]:
            raise ValueError(f"Invalid verification_status '{v}'. Allowed: {allowed}")
        return clean

    @field_validator("authority_type")
    @classmethod
    def validate_authority_type(cls, v: str) -> str:
        allowed = {"statutory", "binding_precedent", "persuasive_authority", "unverified", "user_supplied_provision"}
        clean = v.strip().lower()
        if clean not in [a.lower() for a in allowed]:
            raise ValueError(f"Invalid authority_type '{v}'. Allowed: {allowed}")
        return clean


# ── Draft Content Model ───────────────────────────────────────────────────────
class DraftContent(BaseModel):
    title: str = Field(..., description="Official title of the legal draft")
    sections: List[DraftSection] = Field(default_factory=list, description="Ordered sections of the legal document")
    full_text: str = Field(..., description="Combined plain-text representation of the full draft")

    @model_validator(mode="before")
    @classmethod
    def normalize_full_text(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Compatibility with LLM output returning 'full_draft_text'
            if "full_text" not in data and "full_draft_text" in data:
                data["full_text"] = data["full_draft_text"]
            # If full_text is still missing but sections exist, synthesize full_text deterministically
            if not data.get("full_text") and data.get("sections"):
                secs = data.get("sections", [])
                parts = []
                for s in secs:
                    if isinstance(s, dict):
                        parts.append(str(s.get("content", "")).strip())
                    elif hasattr(s, "content"):
                        parts.append(str(s.content).strip())
                data["full_text"] = "\n\n".join(p for p in parts if p)
        return data

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        if not v or not str(v).strip():
            raise ValueError("Draft title cannot be blank whitespace.")
        return str(v).strip()

    @field_validator("sections")
    @classmethod
    def validate_sections(cls, v: List[DraftSection]) -> List[DraftSection]:
        if not v:
            raise ValueError("DraftContent must contain at least one section.")
        seen_ids = set()
        for sec in v:
            if sec.id in seen_ids:
                raise ValueError(f"Duplicate section ID detected: '{sec.id}'. Section IDs must be unique.")
            seen_ids.add(sec.id)
        return v


# ── Request Model ─────────────────────────────────────────────────────────────
class DraftRequest(BaseModel):
    document_type: Optional[str] = Field(None, description="Canonical document type: 'legal_notice', 'bail_application', 'petition', 'reply'")
    draft_type: Optional[str] = Field(None, description="Backward-compatible alias for document_type")
    subtype: Optional[str] = Field(None, description="Specific document subtype (e.g. 'regular_bail', 'anticipatory_bail', 'writ_petition')")
    case_category: Optional[str] = Field(None, description="Legal domain/category (e.g. Criminal, Commercial, Civil, Constitutional); never silently defaulted")
    facts: Optional[str] = Field(None, description="Core facts and chronology of the dispute/case")
    case_facts: Optional[str] = Field(None, description="Backward-compatible alias for facts")
    target_language: Optional[str] = Field("en", description="Target language ('en', 'hi', 'mr')")
    jurisdiction: Optional[str] = Field(None, description="Court or forum having competence")
    include_citations: bool = Field(True, description="Whether the LLM should suggest relevant statutory provisions or judicial authorities based on case facts (no external retrieval or automated verification performed)")
    case_title: Optional[str] = Field(None, description="Formal caption or title of the matter")
    parties: Optional[Dict[str, Any]] = Field(None, description="Applicant/Sender and Respondent/Recipient details")
    advocate_details: Optional[Dict[str, Any]] = Field(None, description="Advocate name, chambers, enrollment no., phone/email")
    notice_period_days: Optional[str] = Field(None, description="Statutory cure/notice period (e.g. '15 Days', '30 Days', '60 Days')")
    cause_of_action_date: Optional[str] = Field(None, description="Exact date of contract, default, cause of action, or FIR")
    important_dates: Optional[List[str]] = Field(default_factory=list, description="Relevant dates in dispute")
    requested_relief: Optional[str] = Field(None, description="Specific prayer, demands, or relief requested")
    applicable_sections: Optional[List[str]] = Field(default_factory=list, description="Specific statutory sections supplied by user")
    supporting_document_ids: Optional[List[str]] = Field(default_factory=list, description="IDs of uploaded supporting documents (identifiers only; documents are not fetched or read without explicit document access)")

    # Supporting documents are identifiers only; no external retrieval or reading is performed



# ── Response Model ────────────────────────────────────────────────────────────
class DraftResponse(BaseModel):
    draft_id: str
    document_type: str
    subtype: Optional[str] = None
    language: str
    status: str = "completed"
    draft: DraftContent
    citations: List[CitationInfo] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    created_at: str

    # Backward compatibility fields
    draft_text: Optional[str] = None
    translated_text: Optional[str] = None
    citations_used: Optional[List[str]] = None


# ── Section Regeneration Models ───────────────────────────────────────────────
class RegenerateSectionRequest(BaseModel):
    draft_id: Optional[str] = None
    document_type: str
    subtype: Optional[str] = None
    section_id: str
    section_title: str
    current_content: str
    facts: str
    instructions: Optional[str] = None
    language: Optional[str] = "en"
    jurisdiction: Optional[str] = None
    applicable_sections: Optional[List[str]] = Field(default_factory=list)
    requested_relief: Optional[str] = None
    parties: Optional[Dict[str, Any]] = None

    @field_validator("section_id", "section_title", "current_content", "facts")
    @classmethod
    def check_non_blank_regen(cls, v: str, info) -> str:
        if not v or not str(v).strip():
            raise ValueError(f"RegenerateSectionRequest field '{info.field_name}' must not be empty.")
        return str(v).strip()


class RegenerateSectionResponse(BaseModel):
    section_id: str
    section_title: str
    content: str
    citations: List[CitationInfo] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


# ── Translation Models ────────────────────────────────────────────────────────
class TranslateDraftRequest(BaseModel):
    draft_id: Optional[str] = None
    document_type: str
    draft: DraftContent
    source_language: Optional[str] = "en"
    target_language: str = Field(..., description="'en', 'hi', or 'mr'")

    @field_validator("target_language")
    @classmethod
    def validate_target_lang(cls, v: str) -> str:
        clean = v.strip().lower()
        if clean not in SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported target language '{v}'. Supported: 'en', 'hi', 'mr'.")
        return clean


# ── Export Models ─────────────────────────────────────────────────────────────
class ExportDraftRequest(BaseModel):
    title: str = Field(..., description="Official title of the draft document")
    document_type: str = Field(..., description="Canonical document type")
    sections: List[DraftSection] = Field(..., description="Ordered sections of the draft")
    citations: Optional[List[CitationInfo]] = Field(default_factory=list)
    language: Optional[str] = "en"
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    full_text: Optional[str] = None

    @field_validator("title", "document_type")
    @classmethod
    def check_non_empty_export(cls, v: str, info) -> str:
        if not v or not str(v).strip():
            raise ValueError(f"ExportDraftRequest field '{info.field_name}' cannot be empty.")
        return str(v).strip()

    @field_validator("sections")
    @classmethod
    def check_sections_export(cls, v: List[DraftSection]) -> List[DraftSection]:
        if not v:
            raise ValueError("ExportDraftRequest must contain at least one valid section.")
        return v
