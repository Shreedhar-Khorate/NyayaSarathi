from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class RedFlag(BaseModel):
    finding_id: Optional[str] = None
    risk_level: str  # "high" | "medium" | "low"
    risk_category: Optional[str] = "general"
    risk_classification: Optional[str] = "potential_commercial_risk"  # "potential_commercial_risk" | "possible_legal_concern" | "legal_conclusion_requiring_review"
    title: Optional[str] = None
    verbatim_clause: Optional[str] = None
    clause_text: str  # Kept for backward compatibility
    source_page: Optional[int] = None
    page_ref: Optional[int] = 1  # Kept for backward compatibility
    clause_location: Optional[str] = None
    applicable_law: Optional[str] = None
    statutory_provision: Optional[str] = None
    statutory_verification_status: Optional[str] = "unverified"  # "verified" | "unverified" | "not_applicable"
    legal_explanation: Optional[str] = None
    explanation: str  # Kept for backward compatibility
    application_to_clause: Optional[str] = None
    uncertainty_or_limitation: Optional[str] = None
    recommended_action: Optional[str] = None
    recommendation: Optional[str] = None  # Kept for backward compatibility
    evidence_confidence: Optional[float] = None
    confidence: Optional[float] = None  # Kept for backward compatibility


class ScoreBreakdown(BaseModel):
    numerical_score: int = 0
    scoring_method: str = "Weighted Severity Model (High: 5 pts, Medium: 3 pts, Low: 1 pt)"
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    contributing_findings: List[Dict[str, Any]] = Field(default_factory=list)
    risk_rationale: str = ""
    scoring_limitations: Optional[str] = None


class ContractAnalysisResponse(BaseModel):
    filename: Optional[str] = None
    overall_risk_score: str  # "High" | "Medium" | "Low" | "Not Assessed"
    summary: Optional[str] = None
    red_flags: List[RedFlag] = Field(default_factory=list)
    risk_counts: Optional[Dict[str, int]] = Field(default_factory=dict)
    score_breakdown: Optional[ScoreBreakdown] = None
    limitations: Optional[List[str]] = Field(default_factory=list)
    extraction_method: Optional[str] = None
    total_pages: Optional[int] = None
    document_type: Optional[str] = "commercial_contract"
    document_type_label: Optional[str] = "Commercial Contract / Agreement"
    audit_status: Optional[str] = "COMPLETED"  # "COMPLETED" | "DOCUMENT_TYPE_MISMATCH" | "INSUFFICIENT_CONTENT" | "PARTIAL_ANALYSIS" | "FAILED"
    classification_confidence: Optional[float] = None
    classification_reason: Optional[str] = None
    recommended_action: Optional[str] = None
