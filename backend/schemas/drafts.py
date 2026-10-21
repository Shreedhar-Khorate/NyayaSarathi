from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class DraftSection(BaseModel):
    id: str = Field(..., description="Unique section identifier (e.g., 'jurisdiction', 'facts', 'grounds')")
    title: str = Field(..., description="Display title for the legal section")
    content: str = Field(..., description="The substantive drafted text of the section")
    order: int = Field(0, description="Sequential ordering index")


class CitationInfo(BaseModel):
    source_id: Optional[str] = Field(None, description="Identifier linking citation to retrieved evidence chunk (e.g. S1)")
    title: str = Field(..., description="Name of the case or statutory reference")
    citation: str = Field(..., description="Standard formal citation (e.g., 2024 INSC 123 or Section 439 CrPC)")
    court: Optional[str] = Field(None, description="Adjudicating court (e.g., Supreme Court of India, High Court of Bombay)")
    decision_date: Optional[str] = Field(None, description="Date or year of judgment")
    source_url: Optional[str] = Field(None, description="Authentic repository URL or document locator")
    excerpt: str = Field(..., description="Verbatim or authoritative excerpt supporting the legal assertion")
    is_verified: bool = Field(False, description="Whether the citation was verified against authentic case records")
    verification_status: str = Field("verification_required", description="'verified_primary_source' or 'verification_required'")
    authority_type: str = Field("statutory", description="'binding_precedent', 'persuasive_authority', 'statutory', or 'unverified'")
    relevant_statement: Optional[str] = Field(None, description="The legal statement or section supported by this citation")


class DraftContent(BaseModel):
    title: str = Field(..., description="Official title of the legal draft")
    sections: List[DraftSection] = Field(default_factory=list, description="Ordered sections of the legal document")
    full_text: str = Field(..., description="Combined plain-text representation of the full draft")


class DraftRequest(BaseModel):
    document_type: Optional[str] = Field(None, description="Type: 'legal_notice', 'bail_application', 'petition', 'reply'")
    draft_type: Optional[str] = Field(None, description="Backward-compatible alias for document_type")
    case_category: Optional[str] = Field("Civil", description="Field/domain (e.g. Criminal, Civil, Commercial, Constitutional)")
    facts: Optional[str] = Field(None, description="Core facts and chronology of the dispute/case")
    case_facts: Optional[str] = Field(None, description="Backward-compatible alias for facts")
    target_language: Optional[str] = Field("en", description="Target language ('en', 'hi', 'mr')")
    jurisdiction: Optional[str] = Field(None, description="Court or forum having competence")
    include_citations: bool = Field(True, description="Whether to perform legal search and cite statutory/case authority")
    case_title: Optional[str] = Field(None, description="Formal caption or title of the matter")
    parties: Optional[Dict[str, Any]] = Field(None, description="Applicant/Sender and Respondent/Recipient details")
    advocate_details: Optional[Dict[str, Any]] = Field(None, description="Advocate name, chambers, enrollment no., phone/email")
    notice_period_days: Optional[str] = Field("15 Days", description="Statutory cure/notice period (e.g. '15 Days', '30 Days', '60 Days')")
    cause_of_action_date: Optional[str] = Field(None, description="Exact date of contract, default, cause of action, or FIR")
    important_dates: Optional[List[str]] = Field(default_factory=list, description="Relevant dates in dispute")
    requested_relief: Optional[str] = Field(None, description="Specific prayer, demands, or relief requested")
    applicable_sections: Optional[List[str]] = Field(default_factory=list, description="Specific statutory sections supplied")
    supporting_document_ids: Optional[List[str]] = Field(default_factory=list, description="IDs of uploaded supporting documents")


class DraftResponse(BaseModel):
    draft_id: str
    document_type: str
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


class RegenerateSectionRequest(BaseModel):
    draft_id: Optional[str] = None
    document_type: str
    section_id: str
    section_title: str
    current_content: str
    facts: str
    instructions: Optional[str] = None
    language: Optional[str] = "en"
    jurisdiction: Optional[str] = None
    applicable_sections: Optional[List[str]] = Field(default_factory=list)


class RegenerateSectionResponse(BaseModel):
    section_id: str
    section_title: str
    content: str
    citations: List[CitationInfo] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class TranslateDraftRequest(BaseModel):
    draft_id: Optional[str] = None
    document_type: str
    draft: DraftContent
    source_language: Optional[str] = "en"
    target_language: str = Field(..., description="'en', 'hi', or 'mr'")


class ExportDraftRequest(BaseModel):
    title: str
    document_type: str
    sections: List[DraftSection]
    citations: Optional[List[CitationInfo]] = Field(default_factory=list)
    language: Optional[str] = "en"
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
