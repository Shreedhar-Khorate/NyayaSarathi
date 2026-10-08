"""
Prediction Models Re-export Module.
Preserves 100% backward compatibility for all existing imports:
`from models.prediction import ...`

Canonical schema definitions now reside in `schemas.analyze`.
"""

from schemas.analyze import (
    CaseInputRequest,
    AnalyzeRequest,
    CaseAnalysisRequest,
    StructuredCaseProfile,
    CandidateJudgment,
    CandidateRetrievalResponse,
    SimilarityBreakdown,
    RankedPrecedent,
    PrecedentOutcomeValuation,
    HistoricalOutcomeDistribution,
    ProbabilityFormulaMetrics,
    ConfidenceDimensionMetrics,
    AbstentionDecision,
    Stage3OutcomeResponse,
    ConfidencePredictionResult,
    Stage4PredictionResponse,
    VerifiedPrecedent,
    CitationProvenanceReport,
    GroundedExplanation,
    ValidationAuditReport,
    FinalPredictionResponse,
    AnalyzeResponse,
    CaseAnalysisResponse,
)

__all__ = [
    "CaseInputRequest",
    "AnalyzeRequest",
    "CaseAnalysisRequest",
    "StructuredCaseProfile",
    "CandidateJudgment",
    "CandidateRetrievalResponse",
    "SimilarityBreakdown",
    "RankedPrecedent",
    "PrecedentOutcomeValuation",
    "HistoricalOutcomeDistribution",
    "ProbabilityFormulaMetrics",
    "ConfidenceDimensionMetrics",
    "AbstentionDecision",
    "Stage3OutcomeResponse",
    "ConfidencePredictionResult",
    "Stage4PredictionResponse",
    "VerifiedPrecedent",
    "CitationProvenanceReport",
    "GroundedExplanation",
    "ValidationAuditReport",
    "FinalPredictionResponse",
    "AnalyzeResponse",
    "CaseAnalysisResponse",
]
