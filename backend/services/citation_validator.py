"""
Explainable Citation Validator & Exact Source Resolution Engine for NyayaSarathi.

Enforces zero-hallucination citation provenance:
1. Validates citation markers ([S1], [S2], etc.) in the answer against the retrieved evidence pack.
2. Resolves each validated source ID directly to stored document chunks.
3. Retrieves authentic verbatim excerpts, page numbers, paragraph numbers, and document titles from storage.
4. Strips or rejects any hallucinated citation tags not present in retrieved evidence.
"""

import re
from typing import List, Dict, Any, Optional, Set
from pydantic import BaseModel

from services.rag_retrieval import EvidencePack, EvidenceChunk


class ValidatedCitation(BaseModel):
    source_id: str
    document_id: str
    document_title: str
    page_number: int
    paragraph_number: int
    section_title: Optional[str] = None
    excerpt: str
    chunk_id: str


class CitationValidationResult(BaseModel):
    cleaned_answer: str
    citations: List[ValidatedCitation]
    valid_citation_ids: List[str]
    rejected_citation_ids: List[str]


class CitationValidator:
    """
    Validates and resolves citations strictly against stored evidence records.
    """

    def validate_and_resolve(
        self,
        raw_answer: str,
        evidence_pack: EvidencePack,
    ) -> CitationValidationResult:
        """
        Validates citation markers in the generated answer against the retrieved evidence pack.
        Resolves authentic metadata and excerpts directly from storage.
        """
        if not raw_answer:
            return CitationValidationResult(
                cleaned_answer="",
                citations=[],
                valid_citation_ids=[],
                rejected_citation_ids=[],
            )

        # Build lookup table from evidence pack: source_id -> EvidenceChunk
        evidence_map: Dict[str, EvidenceChunk] = {
            chunk.source_id.upper(): chunk for chunk in evidence_pack.chunks
        }

        # Find all citation tags in the answer, e.g. [S1], [S2], [s1]
        matches = re.finditer(r"\[(S\d+)\]", raw_answer, re.IGNORECASE)
        found_source_ids: List[str] = []
        for m in matches:
            tag = m.group(1).upper()
            if tag not in found_source_ids:
                found_source_ids.append(tag)

        valid_source_ids: List[str] = []
        rejected_source_ids: List[str] = []
        validated_citations: List[ValidatedCitation] = []

        for sid in found_source_ids:
            if sid in evidence_map:
                valid_source_ids.append(sid)
                chunk = evidence_map[sid]

                # Extract a concise, authentic excerpt from the chunk text
                excerpt = self._extract_clean_excerpt(chunk.text)

                validated_citations.append(ValidatedCitation(
                    source_id=chunk.source_id,
                    document_id=chunk.document_id,
                    document_title=chunk.document_title,
                    page_number=chunk.page_number,
                    paragraph_number=chunk.paragraph_number,
                    section_title=chunk.section_title,
                    excerpt=excerpt,
                    chunk_id=chunk.chunk_id,
                ))
            else:
                rejected_source_ids.append(sid)

        # If there were rejected citation IDs, remove them from the answer text
        cleaned_answer = raw_answer
        for bad_id in rejected_source_ids:
            cleaned_answer = re.sub(rf"\[{bad_id}\]", "", cleaned_answer, flags=re.IGNORECASE)

        # Clean up any leftover duplicate spaces or punctuation artifacts
        cleaned_answer = re.sub(r" +", " ", cleaned_answer)
        cleaned_answer = re.sub(r" \.", ".", cleaned_answer)

        # If answer contained no citations, but evidence was retrieved and used in fallback, attach top sources
        if not validated_citations and evidence_pack.chunks and not raw_answer.lower().startswith("no relevant"):
            for chunk in evidence_pack.chunks[:3]:
                excerpt = self._extract_clean_excerpt(chunk.text)
                validated_citations.append(ValidatedCitation(
                    source_id=chunk.source_id,
                    document_id=chunk.document_id,
                    document_title=chunk.document_title,
                    page_number=chunk.page_number,
                    paragraph_number=chunk.paragraph_number,
                    section_title=chunk.section_title,
                    excerpt=excerpt,
                    chunk_id=chunk.chunk_id,
                ))
                valid_source_ids.append(chunk.source_id)

        # Sort validated citations by source index (S1, S2, ...)
        validated_citations.sort(
            key=lambda c: int(c.source_id[1:]) if c.source_id[1:].isdigit() else 999
        )

        return CitationValidationResult(
            cleaned_answer=cleaned_answer.strip(),
            citations=validated_citations,
            valid_citation_ids=valid_source_ids,
            rejected_citation_ids=rejected_source_ids,
        )

    def _extract_clean_excerpt(self, full_text: str, max_chars: int = 350) -> str:
        """Pulls a clean, verbatim representative passage without truncation artifacts."""
        if not full_text:
            return ""
        clean = full_text.strip()
        if len(clean) <= max_chars:
            return clean

        # Try to cut at sentence boundary
        cutoff = clean[:max_chars]
        last_period = cutoff.rfind(".")
        if last_period > 100:
            return clean[:last_period + 1]
        return cutoff + "..."


# Singleton
_citation_validator = None

def get_citation_validator() -> CitationValidator:
    global _citation_validator
    if _citation_validator is None:
        _citation_validator = CitationValidator()
    return _citation_validator
