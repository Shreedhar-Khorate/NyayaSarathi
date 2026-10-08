"""
NyayaSarathi Services Package.
Exposes core ML prediction, RAG document processing, search, and domain services.
"""

# ── Core Predictor Pipeline ──────────────────────────────────────────────────
from .dataset_client import get_dataset_client
from .legal_parser import parse_title, normalize_case_type, extract_court_name
from .ingest import ingest_judgments, get_db_stats, search_local_judgments, init_db, get_db_connection
from .case_understanding import get_case_understanding_engine
from .retrieval import get_candidate_retrieval_engine
from .ranking import get_similarity_ranker, get_hybrid_similarity_ranker
from .outcome_engine import get_outcome_analyzer, get_historical_outcome_analyzer
from .calibration import get_probability_calibrator
from .confidence_engine import get_confidence_engine
from .precedent_verifier import get_precedent_verifier
from .explanation_engine import get_explanation_engine
from .validator import get_final_validator
from .analyze_service import predict_case_outcome

# ── Document Intelligence & RAG ──────────────────────────────────────────────
from .document_processor import (
    DocumentProcessor,
    init_document_tables,
    list_user_documents,
    delete_document_by_id,
    get_document_by_id,
)
from .rag_retrieval import get_rag_retrieval_engine, RAGRetrievalEngine
from .citation_validator import get_citation_validator, CitationValidator
from .qa_service import answer_question

# ── Domain Feature Services ──────────────────────────────────────────────────
from .auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)
from .contracts_service import analyze_contract
from .drafts_service import generate_draft
from .statutes_service import map_statute
from .translate_service import translate_legal_text
from .war_room_service import simulate_war_room
from .cases_service import create_case, list_cases, get_case, get_timeline
from .search_service import hybrid_search

# ── Legal OCR Subsystem ──────────────────────────────────────────────────────
from .ocr import (
    LegalOCRProcessor,
    DocumentDetector,
    PDFExtractor,
    DOCXExtractor,
    ImageExtractor,
    ImagePreprocessor,
    OCREngine,
    LayoutAnalyzer,
    ReadingOrder,
)

__all__ = [
    # Predictor & Analysis
    "get_dataset_client",
    "parse_title",
    "normalize_case_type",
    "extract_court_name",
    "ingest_judgments",
    "get_db_stats",
    "search_local_judgments",
    "init_db",
    "get_db_connection",
    "get_case_understanding_engine",
    "get_candidate_retrieval_engine",
    "get_similarity_ranker",
    "get_hybrid_similarity_ranker",
    "get_outcome_analyzer",
    "get_historical_outcome_analyzer",
    "get_probability_calibrator",
    "get_confidence_engine",
    "get_precedent_verifier",
    "get_explanation_engine",
    "get_final_validator",
    "predict_case_outcome",
    # RAG & Documents
    "DocumentProcessor",
    "init_document_tables",
    "list_user_documents",
    "delete_document_by_id",
    "get_document_by_id",
    "get_rag_retrieval_engine",
    "RAGRetrievalEngine",
    "get_citation_validator",
    "CitationValidator",
    "answer_question",
    # Features
    "hash_password",
    "verify_password",
    "create_access_token",
    "decode_access_token",
    "analyze_contract",
    "generate_draft",
    "map_statute",
    "translate_legal_text",
    "simulate_war_room",
    "create_case",
    "list_cases",
    "get_case",
    "get_timeline",
    "hybrid_search",
    # Legal OCR
    "LegalOCRProcessor",
    "DocumentDetector",
    "PDFExtractor",
    "DOCXExtractor",
    "ImageExtractor",
    "ImagePreprocessor",
    "OCREngine",
    "LayoutAnalyzer",
    "ReadingOrder",
]
