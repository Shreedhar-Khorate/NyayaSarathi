"""
Unified Data Models for NyayaSarathi Judgment Success Predictor.
Consolidates all request, response, precedent, probability, confidence,
and validation schemas into a single clean module.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any, Union
import re


# ── 1. Request Models ────────────────────────────────────────────────────────

class CaseInputRequest(BaseModel):
    """User case input for judgment success prediction."""
    description: str = Field(..., description="Narrative facts of the case")
    case_type: Optional[str] = Field(None, description="Optional category (e.g. bail, contract, motor_accident)")
    court: Optional[str] = Field(None, description="Target court or jurisdiction (e.g. Patna High Court)")
    acts: Optional[Union[List[str], str]] = Field(default_factory=list, description="Applicable Indian Acts")
    sections: Optional[Union[List[str], str]] = Field(default_factory=list, description="Applicable statutory sections")
    user_position: Optional[str] = Field(None, description="applicant, petitioner, appellant, respondent, defendant")

    @field_validator("sections", mode="before")
    @classmethod
    def parse_sections(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            return [s.strip() for s in re.split(r"[,;\n]+", v) if s.strip()]
        return v

    @field_validator("acts", mode="before")
    @classmethod
    def parse_acts(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            return [s.strip() for s in re.split(r"[,;\n]+", v) if s.strip()]
        return v


# Aliases for backward compatibility
AnalyzeRequest = CaseInputRequest
CaseAnalysisRequest = CaseInputRequest


# ── 2. Case Profiling & Ranking Models ───────────────────────────────────────

class StructuredCaseProfile(BaseModel):
    """Structured legal profile extracted from the case narrative."""
    case_type: str
    legal_domain: str
    detected_acts: List[str] = Field(default_factory=list)
    detected_sections: List[str] = Field(default_factory=list)
    key_facts: List[str] = Field(default_factory=list)
    legal_issues: List[str] = Field(default_factory=list)
    user_position: str
    classification_confidence: float
    extracted_court: Optional[str] = None


class CandidateJudgment(BaseModel):
    """Candidate judgment retrieved from database for ranking."""
    cnr: str
    title: str
    court: str
    year: Optional[int] = None
    decision_date: Optional[str] = None
    case_type: str
    disposal_nature: Optional[str] = None
    disposal_nature_normalized: Optional[str] = None
    matched_sections: List[str] = Field(default_factory=list)
    matched_acts: List[str] = Field(default_factory=list)
    text_snippet: Optional[str] = None
    retrieval_tier: Optional[str] = "Tier 1"
    source_url: Optional[str] = None


class CandidateRetrievalResponse(BaseModel):
    """Candidate retrieval response metadata."""
    status: str = "success"
    query_summary: Dict[str, Any] = Field(default_factory=dict)
    total_candidates_found: int = 0
    retrieval_tiers_used: List[str] = Field(default_factory=list)
    candidates: List[CandidateJudgment] = Field(default_factory=list)


class SimilarityBreakdown(BaseModel):
    """Transparent similarity scoring attribution."""
    semantic_score: float
    statutory_boost: float
    court_match_boost: float
    final_similarity: float


class RankedPrecedent(BaseModel):
    """Ranked precedent with similarity attribution."""
    cnr: str
    case_name: str
    court: str
    year: Optional[int] = None
    case_type: str
    outcome: str
    similarity: float
    score_breakdown: SimilarityBreakdown
    matched_sections: List[str] = Field(default_factory=list)
    matched_acts: List[str] = Field(default_factory=list)
    excerpt: str
    decision_date: Optional[str] = None
    source_url: Optional[str] = None


# ── 3. Outcome & Mathematical Telemetry Models ──────────────────────────────

class PrecedentOutcomeValuation(BaseModel):
    """Position-adjusted outcome valuation for a precedent."""
    cnr: str
    case_name: str
    court: str
    year: Optional[int] = None
    raw_outcome: str
    user_position: str
    favorable_score: float
    outcome_label: str
    similarity: float
    weight: float
    weighted_contribution: float


class HistoricalOutcomeDistribution(BaseModel):
    """Outcome breakdown across retrieved precedents."""
    total_precedents: int
    favorable_count: int
    unfavorable_count: int
    partially_favorable_count: int
    neutral_count: int
    unweighted_favorable_rate_pct: float


class ProbabilityFormulaMetrics(BaseModel):
    """Dirichlet mathematical telemetry details."""
    sum_of_weights: float
    sum_of_weighted_scores: float
    prior_smoothing_alpha: float
    prior_baseline: float
    raw_calculated_probability_pct: float
    calibrated_probability_pct: float
    formula_expression: str


# ── 4. Confidence & Abstention Models ────────────────────────────────────────

class ConfidenceDimensionMetrics(BaseModel):
    """Multi-dimensional confidence scores [0.0 - 1.0]."""
    sample_size_score: float
    similarity_density_score: float
    statutory_alignment_score: float
    outcome_consistency_score: float
    aggregate_confidence_score: float
    confidence_rating: str


class AbstentionDecision(BaseModel):
    """Mandatory abstention evaluation."""
    should_abstain: bool
    reason_code: Optional[str] = None
    explanation: str


class Stage3OutcomeResponse(BaseModel):
    """Outcome engine prediction result."""
    status: str
    case_type: str
    user_position: str
    success_probability: int
    predicted_verdict: str
    precedent_valuations: List[PrecedentOutcomeValuation]
    outcome_distribution: HistoricalOutcomeDistribution
    probability_metrics: ProbabilityFormulaMetrics
    message: str


class ConfidencePredictionResult(BaseModel):
    """Intermediate confidence and probability evaluation result."""
    status: str
    case_type: str
    user_position: str
    success_probability: Optional[int] = None
    predicted_verdict: Optional[str] = None
    confidence: str
    confidence_breakdown: ConfidenceDimensionMetrics
    abstention_info: Optional[AbstentionDecision] = None
    precedents: List[RankedPrecedent] = Field(default_factory=list)
    precedent_valuations: List[PrecedentOutcomeValuation] = Field(default_factory=list)
    outcome_distribution: Optional[HistoricalOutcomeDistribution] = None
    probability_metrics: Optional[ProbabilityFormulaMetrics] = None
    structured_case: StructuredCaseProfile
    message: str


# Alias for backward compatibility
Stage4PredictionResponse = ConfidencePredictionResult


# ── 5. Verified Precedent & Citation Models ─────────────────────────────────

class VerifiedPrecedent(BaseModel):
    """Verified Indian court precedent with authentic CNR and verbatim excerpt."""
    case_name: str
    court: str
    bench: Optional[str] = None
    judge: Optional[str] = None
    year: Optional[int] = None
    decision_date: Optional[str] = None
    similarity: float
    outcome: str
    favorable_to_user: str
    cnr: str
    citation: str
    source_url: str
    matched_sections: List[str] = Field(default_factory=list)
    matched_acts: List[str] = Field(default_factory=list)
    verbatim_excerpt: str
    is_verified: bool = True


class CitationProvenanceReport(BaseModel):
    """Provenance report confirming 100% database verification."""
    total_precedents_verified: int
    database_provenance: str = "NyayaSarathi Local SQLite Judgment Archive"
    dataset_origin: str = "overthelex/indian-court-decisions (Hugging Face)"
    zero_hallucination_guaranteed: bool = True
    verified_cnrs: List[str] = Field(default_factory=list)


# ── 6. Grounded Explanation & Validation Models ─────────────────────────────

class GroundedExplanation(BaseModel):
    """Synthesized natural language explanation grounded in retrieved evidence."""
    takeaway: str
    supporting_factors: List[str] = Field(default_factory=list)
    opposing_factors: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    synthesis_engine: str = "NyayaSarathi Grounded Legal Synthesizer"


class ValidationAuditReport(BaseModel):
    """Post-generation integrity audit report."""
    is_valid: bool
    precedent_checks_passed: bool = True
    citation_checks_passed: bool = True
    math_integrity_passed: bool = True
    claims_grounded: bool = True
    validation_timestamp: Optional[str] = None


# ── 7. Final Response Model ─────────────────────────────────────────────────

class FinalPredictionResponse(BaseModel):
    """Master NyayaSarathi Judgment Success Predictor Response."""
    status: str = Field(..., description="'success' or 'insufficient_data'")
    success_probability: Optional[int] = Field(None, description="Data-driven probability [5% - 95%]")
    confidence: str = Field(..., description="'high', 'medium', or 'low'")
    case_type: str = Field(..., description="Categorized Indian legal domain")
    predicted_outcome: Optional[str] = Field(None, description="'favorable', 'unfavorable', or 'balanced / discretionary'")
    supporting_factors: List[str] = Field(default_factory=list)
    opposing_factors: List[str] = Field(default_factory=list)
    precedents: List[VerifiedPrecedent] = Field(default_factory=list)
    takeaway: str = Field(...)
    limitations: List[str] = Field(default_factory=list)
    provenance_report: Optional[CitationProvenanceReport] = None
    validation_report: Optional[ValidationAuditReport] = None
    structured_case: Optional[StructuredCaseProfile] = None
    disclaimer: str = (
        "This is an AI-generated advisory estimate based on historical judgments "
        "and is not a guarantee or final legal opinion."
    )

    # Backward compatibility aliases
    probability: Optional[str] = None
    outcome: Optional[str] = None
    legalPrecedents: Optional[List[str]] = None
    keyTakeaway: Optional[str] = None


# Aliases for backward compatibility
AnalyzeResponse = FinalPredictionResponse
CaseAnalysisResponse = FinalPredictionResponse
