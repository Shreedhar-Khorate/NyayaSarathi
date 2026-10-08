"""
NyayaSarathi Schemas Package.
Exports all Pydantic request, response, and transfer models for the API.
"""

from .analyze import (
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

from .auth import (
    SignupRequest,
    LoginRequest,
    UserProfile,
    AuthTokenResponse,
)

from .cases import (
    Deadline,
    Case,
    CreateCaseRequest,
    TimelineEvent,
    TimelineResponse,
)

from .contracts import (
    RedFlag,
    ContractAnalysisResponse,
)

from .drafts import (
    DraftRequest,
    DraftResponse,
)

from .qa import (
    QARequest,
    Citation,
    QAResponse,
    DocumentMetadata,
    DocumentListResponse,
    ChunkMetadata,
    DocumentDetailResponse,
)

from .search import (
    SearchRequest,
    SearchResult,
    SearchResponse,
)

from .statutes import (
    StatuteMapResponse,
)

from .translate import (
    TranslationRequest,
    TranslationResponse,
)

from .war_room import (
    WarRoomRequest,
    WarRoomResponse,
)

from .ocr import (
    Block,
    PageData,
    OCRDocumentResponse,
    DocumentResponse,
)

__all__ = [
    # Analyze / Predictor
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
    # Auth
    "SignupRequest",
    "LoginRequest",
    "UserProfile",
    "AuthTokenResponse",
    # Cases
    "Deadline",
    "Case",
    "CreateCaseRequest",
    "TimelineEvent",
    "TimelineResponse",
    # Contracts
    "RedFlag",
    "ContractAnalysisResponse",
    # Drafts
    "DraftRequest",
    "DraftResponse",
    # QA
    "QARequest",
    "Citation",
    "QAResponse",
    "DocumentMetadata",
    "DocumentListResponse",
    "ChunkMetadata",
    "DocumentDetailResponse",
    # Search
    "SearchRequest",
    "SearchResult",
    "SearchResponse",
    # Statutes
    "StatuteMapResponse",
    # Translate
    "TranslationRequest",
    "TranslationResponse",
    # War Room
    "WarRoomRequest",
    "WarRoomResponse",
    # Legal Document OCR
    "Block",
    "PageData",
    "OCRDocumentResponse",
    "DocumentResponse",
]
