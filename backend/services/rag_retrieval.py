"""
Modular Hybrid Retrieval Engine for NyayaSarathi RAG Q&A.
Combines:
1. Okapi BM25 Lexical Keyword Search
2. Dense Semantic Vector Search (Cosine Similarity)
3. Reciprocal Rank Fusion (RRF, k=60)
4. Document Ownership & Security Access Validation
5. Verifiable Evidence Pack Construction ([S1], [S2], ...)
"""

import math
import re
import sqlite3
import numpy as np
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from rank_bm25 import BM25Okapi

from services.document_processor import _get_db_connection


class EvidenceChunk(BaseModel):
    source_id: str  # e.g. "S1", "S2"
    chunk_id: str
    document_id: str
    document_title: str
    page_number: int
    paragraph_number: int
    section_title: Optional[str] = None
    text: str
    rrf_score: float
    bm25_score: float
    vector_score: float


class EvidencePack(BaseModel):
    question: str
    document_ids: List[str]
    chunks: List[EvidenceChunk]
    has_sufficient_evidence: bool = True


class RAGRetrievalEngine:
    """
    Executes secure, document-scoped Hybrid BM25 + Vector Retrieval with Reciprocal Rank Fusion.
    """

    def __init__(self, rrf_k: int = 60, vector_weight: float = 0.5, bm25_weight: float = 0.5):
        self.rrf_k = rrf_k
        self.vector_weight = vector_weight
        self.bm25_weight = bm25_weight

    def retrieve_evidence(
        self,
        question: str,
        document_ids: List[str],
        user_id: Optional[str] = None,
        top_k: int = 6,
    ) -> EvidencePack:
        """
        Retrieves the top-k most relevant evidence chunks across the selected documents.
        """
        if not question or not question.strip():
            return EvidencePack(question="", document_ids=document_ids, chunks=[], has_sufficient_evidence=False)

        if not document_ids:
            return EvidencePack(question=question, document_ids=[], chunks=[], has_sufficient_evidence=False)

        # 1. Fetch chunks for authorized documents
        conn = _get_db_connection()
        try:
            placeholders = ",".join(["?"] * len(document_ids))
            query_sql = f"""
                SELECT 
                    c.id as chunk_id,
                    c.document_id,
                    c.chunk_index,
                    c.page_number,
                    c.paragraph_number,
                    c.section_title,
                    c.text,
                    c.user_id,
                    d.title as document_title,
                    d.user_id as doc_user_id
                FROM rag_chunks c
                JOIN rag_documents d ON c.document_id = d.id
                WHERE c.document_id IN ({placeholders})
            """
            rows = conn.execute(query_sql, document_ids).fetchall()
        finally:
            conn.close()

        if not rows:
            return EvidencePack(question=question, document_ids=document_ids, chunks=[], has_sufficient_evidence=False)

        # 2. Filter by user authorization if user_id is provided
        authorized_rows = []
        for r in rows:
            row_dict = dict(r)
            doc_user = row_dict.get("doc_user_id")
            if user_id and doc_user and doc_user != user_id:
                continue  # Skip unauthorized document chunk
            authorized_rows.append(row_dict)

        if not authorized_rows:
            return EvidencePack(question=question, document_ids=document_ids, chunks=[], has_sufficient_evidence=False)

        chunk_texts = [r["text"] for r in authorized_rows]
        n_chunks = len(chunk_texts)

        # 3. BM25 Lexical Scoring & Stemmed Term Overlap
        tokenized_corpus = [self._tokenize(t) for t in chunk_texts]
        query_tokens = self._tokenize(question)

        # Stop words to ignore for overlap scoring
        stop_words = {"the", "and", "for", "with", "from", "that", "this", "what", "which", "where", "when", "were", "been", "have", "does", "about", "under"}
        content_query_words = [w for w in query_tokens if w not in stop_words and len(w) > 2]
        query_stems = {w.rstrip("s") for w in content_query_words}

        overlap_scores = np.zeros(n_chunks, dtype=float)
        if query_stems:
            for i, doc_toks in enumerate(tokenized_corpus):
                doc_stems = {w.rstrip("s") for w in doc_toks}
                hits = len(query_stems.intersection(doc_stems))
                overlap_scores[i] = hits / len(query_stems)

        bm25_scores = np.zeros(n_chunks, dtype=float)
        if query_tokens and any(tokenized_corpus):
            try:
                bm25_model = BM25Okapi(tokenized_corpus)
                raw_bm25 = np.clip(np.array(bm25_model.get_scores(query_tokens)), 0.0, None)
                max_bm25 = np.max(raw_bm25) if len(raw_bm25) > 0 else 0
                if max_bm25 > 0:
                    bm25_scores = raw_bm25 / max_bm25
            except Exception:
                pass

        # Fuse BM25 with overlap score
        combined_lexical_scores = np.maximum(bm25_scores, overlap_scores)

        # 4. Dense Vector Cosine Similarity
        vector_scores = np.zeros(n_chunks, dtype=float)
        try:
            tfidf = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", sublinear_tf=True)
            tfidf_matrix = tfidf.fit_transform([question] + chunk_texts)
            q_vec = tfidf_matrix[0:1]
            doc_vecs = tfidf_matrix[1:]
            sims = cosine_similarity(q_vec, doc_vecs)[0]
            vector_scores = np.clip(sims, 0.0, 1.0)
        except Exception:
            pass

        # 5. Compute Reciprocal Rank Fusion (RRF)
        # Sort indices for ranking
        lex_rank_indices = np.argsort(-combined_lexical_scores)
        vector_rank_indices = np.argsort(-vector_scores)

        lex_ranks = {idx: rank for rank, idx in enumerate(lex_rank_indices, start=1)}
        vector_ranks = {idx: rank for rank, idx in enumerate(vector_rank_indices, start=1)}

        scored_candidates = []
        for i in range(n_chunks):
            r_lex = lex_ranks[i]
            r_vec = vector_ranks[i]
            rrf_score = (self.bm25_weight / (self.rrf_k + r_lex)) + (self.vector_weight / (self.rrf_k + r_vec))
            scored_candidates.append({
                "index": i,
                "row": authorized_rows[i],
                "rrf_score": float(rrf_score),
                "bm25_score": float(combined_lexical_scores[i]),
                "vector_score": float(vector_scores[i]),
            })

        # 6. Filter only truly relevant candidates (must have keyword hit or semantic vector match)
        relevant_candidates = [
            c for c in scored_candidates
            if c["bm25_score"] > 0.0 or c["vector_score"] > 0.04
        ]

        # Sort by RRF score descending
        relevant_candidates.sort(key=lambda x: x["rrf_score"], reverse=True)

        # 7. Select top_k and build EvidencePack
        evidence_chunks: List[EvidenceChunk] = []
        for rank, cand in enumerate(relevant_candidates[:top_k], start=1):
            source_id = f"S{rank}"
            row = cand["row"]
            evidence_chunks.append(EvidenceChunk(
                source_id=source_id,
                chunk_id=row["chunk_id"],
                document_id=row["document_id"],
                document_title=row["document_title"] or "Legal Document",
                page_number=row["page_number"] or 1,
                paragraph_number=row["paragraph_number"] or 1,
                section_title=row.get("section_title"),
                text=row["text"],
                rrf_score=round(cand["rrf_score"], 4),
                bm25_score=round(cand["bm25_score"], 4),
                vector_score=round(cand["vector_score"], 4),
            ))

        has_sufficient = len(evidence_chunks) > 0

        return EvidencePack(
            question=question,
            document_ids=document_ids,
            chunks=evidence_chunks,
            has_sufficient_evidence=has_sufficient,
        )

    def _tokenize(self, text: str) -> List[str]:
        if not text:
            return []
        return re.findall(r"\b[a-zA-Z0-9_\-\.]{2,}\b", text.lower())


# Singleton
_rag_retrieval_engine = None

def get_rag_retrieval_engine() -> RAGRetrievalEngine:
    global _rag_retrieval_engine
    if _rag_retrieval_engine is None:
        _rag_retrieval_engine = RAGRetrievalEngine()
    return _rag_retrieval_engine
