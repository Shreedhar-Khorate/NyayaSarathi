"""
NyayaSarathi Legal War Room — Pydantic Schemas
Comprehensive data contracts for case overview, fact sheet, evidence analysis,
argument builder, opposition simulation, legal precedents, and strategy reports.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


# ── Fact Sheet ────────────────────────────────────────────────────────────────
class FactItem(BaseModel):
    id: str
    fact: str
    category: str = Field(
        ...,
        description="One of: 'procedural_event', 'court_finding', 'final_holding', 'documentary_evidence', 'witness_testimony', 'party_submission', 'allegation'"
    )
    source_doc_id: Optional[str] = None
    source_doc_title: Optional[str] = None
    page_number: Optional[int] = None
    paragraph_number: Optional[int] = None
    excerpt: Optional[str] = None
    verification_status: str = Field(
        "reported_in_judgment",
        description="'verified_from_primary_record', 'reported_in_judgment', 'unverified_submission', 'verification_required'"
    )
    source_reliability: str = Field(
        "official_court_record",
        description="'primary_judicial_record', 'official_court_record', 'contemporaneous_document', 'party_pleading', 'unverified_claim'"
    )
    confidence: float = 0.90
    is_reviewed: bool = False
    is_custom: bool = False


# ── Evidence Findings ─────────────────────────────────────────────────────────
class EvidenceFinding(BaseModel):
    id: str
    finding: str
    underlying_fact: Optional[str] = None
    relevant_claim: str
    evidence_type: str = Field(
        ...,
        description="'documentary', 'testimonial', 'statutory_record', 'inconsistent_statement', 'missing_document', 'court_record'"
    )
    source_reliability: str = Field(
        "official_court_record",
        description="'primary_judicial_record', 'official_court_record', 'contemporaneous_document', 'party_pleading', 'unverified_claim'"
    )
    evidentiary_status: str = Field(
        "established",
        description="'established', 'disputed', 'corroborated_by_record', 'unsupported', 'inadmissible', 'verification_required'"
    )
    legal_relevance: str = Field(
        "direct_probative",
        description="'direct_probative', 'contextual_procedural', 'impeachment', 'peripheral'"
    )
    source_doc_id: Optional[str] = None
    source_doc_title: Optional[str] = None
    page_number: Optional[int] = None
    paragraph_number: Optional[int] = None
    excerpt: Optional[str] = None
    model_confidence: float = Field(0.85, description="Model extraction confidence score (0.0 to 1.0)")
    confidence: float = 0.85
    follow_up_question: Optional[str] = None
    is_disputed: bool = False


# ── Argument Builder ──────────────────────────────────────────────────────────
class LegalArgument(BaseModel):
    id: str
    title: str
    legal_issue: Optional[str] = None
    main_claim: str
    procedural_role_argument: Optional[str] = None
    supporting_facts: List[str] = []
    evidence_refs: List[str] = []
    evidence_still_required: List[str] = []
    applicable_provisions: List[str] = []  # e.g. ["Statutory Section / Rule"]
    relevant_precedents: List[str] = []  # e.g. ["Citation / Case Name"]
    legal_reasoning: str
    strongest_opposing_argument: Optional[str] = None
    rebuttal_and_weaknesses: Optional[str] = None
    reasoning_type: str = Field("actual_judicial_reasoning", description="'actual_judicial_reasoning' or 'proposed_advocacy_argument'")
    potential_weaknesses: List[str] = []
    questions_to_investigate: List[str] = []
    is_reviewed: bool = False
    is_custom: bool = False
    created_at: Optional[str] = None


# ── Opposition Simulator (Devil's Advocate) ──────────────────────────────────
class OppositionArgument(BaseModel):
    id: str
    opposing_claim: str
    supporting_facts_evidence: List[str] = []
    adverse_precedents: List[str] = []
    user_position_weaknesses: List[str] = []
    suggested_rebuttal_counterarguments: List[str] = []
    missing_information: List[str] = []
    is_reviewed: bool = False


# ── Risk and Weakness Assessment ──────────────────────────────────────────────
class RiskAssessmentItem(BaseModel):
    id: str
    risk_type: str = Field(
        ...,
        description="'unsupported_argument', 'missing_evidence', 'unresolved_factual_dispute', 'adverse_precedent', 'weak_evidence_link', 'requires_expert_review'"
    )
    description: str
    severity: str = Field("medium", description="'high', 'medium', 'low'")
    affected_claims: List[str] = []
    mitigation_steps: List[str] = []
    clarification_documents_needed: List[str] = []


# ── Legal Precedent Research ──────────────────────────────────────────────────
class PrecedentFinding(BaseModel):
    cnr: str
    title: str
    court: str
    citation: Optional[str] = None
    decision_date: Optional[str] = None
    outcome_type: str = Field(
        "supporting",
        description="'supporting', 'adverse', 'distinguishable', 'inconclusive', 'verification_required'"
    )
    legal_issue: str
    relevant_paragraphs: Optional[str] = None
    procedural_context: Optional[str] = None
    actual_holding: str
    verbatim_excerpt: str
    relevance_explanation: str
    binding_persuasive_nature: str = "Binding Authority"
    verification_status: str = Field("verified_primary_source", description="'verified_primary_source' or 'verification_required'")
    source_url: Optional[str] = None


# ── Comprehensive Strategy Report (10 Structured Sections) ────────────────────
class StrategyReport(BaseModel):
    executive_summary: str = ""
    parties_and_procedural_posture: str = ""
    parties_and_issues: str = ""  # Backward compat
    verified_factual_chronology: str = ""
    factual_chronology: str = ""  # Backward compat
    issues_for_determination: str = ""
    evidence_matrix: str = ""
    evidence_analysis: str = ""  # Backward compat
    arguments_and_counterarguments: str = ""
    affirmative_arguments: str = ""  # Backward compat
    opposition_stress_test: str = ""
    precedent_landscape: str = ""
    risks_evidentiary_gaps_questions: str = ""
    risks_and_weaknesses: str = ""  # Backward compat
    unresolved_questions: str = ""
    practical_next_steps: str = ""
    action_plan: str = ""  # Backward compat
    limitations_and_verification_warnings: str = ""
    disclaimer: str = (
        "NyayaSarathi Legal War Room is an AI-assisted legal intelligence tool designed strictly for research, "
        "evidence synthesis, and case preparation. It does not provide legal advice, guarantee court outcomes, "
        "or replace qualified professional legal counsel."
    )
    generated_at: Optional[str] = None


# ── Session Management ────────────────────────────────────────────────────────
class RelevantDate(BaseModel):
    event_date: str
    description: str
    source_reference: Optional[str] = None


class WarRoomSessionCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    case_type: Optional[str] = "general"
    jurisdiction: Optional[str] = "High Court"
    court: Optional[str] = ""
    user_position: Optional[str] = "petitioner"
    opposing_party: Optional[str] = ""
    relevant_dates: Optional[List[RelevantDate]] = []
    selected_doc_ids: Optional[List[str]] = []


class WarRoomSessionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    case_type: Optional[str] = None
    jurisdiction: Optional[str] = None
    court: Optional[str] = None
    user_position: Optional[str] = None
    opposing_party: Optional[str] = None
    relevant_dates: Optional[List[Dict[str, Any]]] = None
    selected_doc_ids: Optional[List[str]] = None
    fact_sheet: Optional[List[Dict[str, Any]]] = None
    evidence_findings: Optional[List[Dict[str, Any]]] = None
    arguments: Optional[List[Dict[str, Any]]] = None
    opposition: Optional[List[Dict[str, Any]]] = None
    risks: Optional[List[Dict[str, Any]]] = None
    precedents: Optional[List[Dict[str, Any]]] = None
    report: Optional[Dict[str, Any]] = None


class WarRoomSessionResponse(BaseModel):
    id: str
    user_id: Optional[str] = None
    title: str
    description: str
    case_type: str
    jurisdiction: str
    court: str
    user_position: str
    opposing_party: str
    relevant_dates: List[Dict[str, Any]] = []
    selected_doc_ids: List[str] = []
    fact_sheet: List[Dict[str, Any]] = []
    evidence_findings: List[Dict[str, Any]] = []
    arguments: List[Dict[str, Any]] = []
    opposition: List[Dict[str, Any]] = []
    risks: List[Dict[str, Any]] = []
    precedents: List[Dict[str, Any]] = []
    report: Dict[str, Any] = {}
    version: int = 1
    created_at: str
    updated_at: str


# ── Analysis Operations ───────────────────────────────────────────────────────
class WarRoomAnalyzeRequest(BaseModel):
    operation: str = Field(
        ...,
        description="One of: 'facts', 'evidence', 'arguments', 'opposition', 'risks', 'precedents', 'report'"
    )
    target_id: Optional[str] = Field(None, description="Optional target argument_id or section to regenerate")
    force_refresh: bool = False
    custom_instructions: Optional[str] = None


class WarRoomAnalyzeResponse(BaseModel):
    operation: str
    session_id: str
    result: Any
    cache_hit: bool = False
    provider: str = "system"
    model: str = "none"
    tokens_used: int = 0
    duration_ms: int = 0
    message: Optional[str] = None


# ── Backward Compatibility Stubs ──────────────────────────────────────────────
class WarRoomRequest(BaseModel):
    position: str
    rounds: int = 3


class WarRoomResponse(BaseModel):
    counter_arguments: List[str]
    weaknesses_identified: List[str]
    suggested_reinforcements: List[str]
