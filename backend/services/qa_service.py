"""
RAG Legal Q&A Service for NyayaSarathi.
Orchestrates:
1. Hybrid BM25 + Vector Retrieval scoped strictly to user-selected documents
2. LLM Provider Manager execution (Groq / Cerebras / Ollama)
3. Exact citation validation against stored chunk database
4. Zero-hallucination explainable response assembly
"""

import os
import re
import logging
from typing import List, Optional, Dict, Any

from schemas.qa import QARequest, QAResponse, Citation
from services.rag_retrieval import get_rag_retrieval_engine, EvidencePack
from services.llm.provider_manager import get_llm_provider_manager
from services.citation_validator import get_citation_validator
from services.document_processor import list_user_documents

logger = logging.getLogger("nyayasarathi.qa_service")


def answer_question(request: QARequest, user_id: Optional[str] = None) -> QAResponse:
    """
    Executes end-to-end evidence retrieval, multi-provider LLM generation,
    and exact source citation verification strictly from uploaded documents.
    """
    question = request.question.strip()
    doc_ids = request.document_ids or []

    # If no specific documents were provided, scope to user's indexed documents
    if not doc_ids:
        docs = list_user_documents(user_id)
        indexed_docs = [d["id"] for d in docs if d["status"] == "indexed"]
        doc_ids = indexed_docs

    if not doc_ids:
        return QAResponse(
            answer="No legal documents are currently uploaded or selected. Please click 'Upload Document' to upload a PDF, DOCX, or TXT legal record, or select an indexed document to begin research.",
            citations=[],
            insufficient_evidence=True,
            provider="system",
            model="none",
        )

    retrieval_engine = get_rag_retrieval_engine()
    llm_manager = get_llm_provider_manager()
    citation_validator = get_citation_validator()

    # 1. Retrieve hybrid evidence from selected documents
    evidence_pack: EvidencePack = retrieval_engine.retrieve_evidence(
        question=question,
        document_ids=doc_ids,
        user_id=user_id,
        top_k=6,
    )

    if not evidence_pack.chunks:
        return QAResponse(
            answer="Based on the selected documents, no relevant passages or facts could be found to answer this inquiry. The uploaded text does not appear to contain sufficient information regarding your question.",
            citations=[],
            insufficient_evidence=True,
            provider="system",
            model="none",
        )

    # Convert chunks to dicts for LLM prompt builder
    chunk_dicts = [
        {
            "source_id": c.source_id,
            "chunk_id": c.chunk_id,
            "document_id": c.document_id,
            "document_title": c.document_title,
            "page_number": c.page_number,
            "paragraph_number": c.paragraph_number,
            "section_title": c.section_title,
            "text": c.text,
        }
        for c in evidence_pack.chunks
    ]

    # 2. Generate answer via dedicated Research Gemini Key (Gemini API 3) or Provider Manager fallback
    research_key = (
        os.environ.get("RESEARCH_GEMINI_API_KEY", "").strip()
        or os.environ.get("GEMINI_API_KEY", "").strip()
    )
    llm_result = None
    if research_key:
        try:
            from services.llm.gemini_provider import GeminiProvider
            model_name = os.environ.get("RESEARCH_GEMINI_MODEL", os.environ.get("GEMINI_MODEL", "gemini-1.5-flash"))
            gemini_prov = GeminiProvider(api_key=research_key, model=model_name)
            system_prompt = (
                "You are NyayaSarathi's Senior Legal Research Intelligence Assistant.\n"
                "Answer the user's legal question strictly and truthfully using the retrieved evidence passages.\n"
                "CRITICAL RULES:\n"
                "1. Every factual assertion must be cited with its corresponding bracket notation, e.g. [S1], [S2].\n"
                "2. Do not invent facts, citations, or precedents not present in the evidence.\n"
                "3. If evidence is insufficient, state clearly that the provided legal documents do not contain sufficient information."
            )
            user_prompt = llm_manager._build_user_prompt(question, chunk_dicts)
            llm_result = gemini_prov.generate_grounded_answer(
                question=question,
                evidence_chunks=chunk_dicts,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                timeout_seconds=25.0,
            )
        except Exception as e:
            logger.warning(f"Research Gemini call failed, falling back to Provider Manager: {e}")

    if not llm_result:
        llm_result = llm_manager.generate_grounded_answer(
            question=question,
            evidence_chunks=chunk_dicts,
        )

    # 3. Validate citations and resolve stored excerpt provenance
    validation_result = citation_validator.validate_and_resolve(
        raw_answer=llm_result.answer,
        evidence_pack=evidence_pack,
    )

    # Map to API Citation schema
    api_citations: List[Citation] = [
        Citation(
            source_id=vc.source_id,
            document_id=vc.document_id,
            document_title=vc.document_title,
            page_number=vc.page_number,
            paragraph_number=vc.paragraph_number,
            section_title=vc.section_title,
            excerpt=vc.excerpt,
            chunk_id=vc.chunk_id,
        )
        for vc in validation_result.citations
    ]

    return QAResponse(
        answer=validation_result.cleaned_answer,
        citations=api_citations,
        insufficient_evidence=llm_result.insufficient_evidence,
        provider=llm_result.provider,
        model=llm_result.model,
    )
