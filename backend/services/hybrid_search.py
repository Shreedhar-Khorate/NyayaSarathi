"""
Hybrid Search & Reciprocal Rank Fusion (RRF) Engine for NyayaSarathi.

Combines:
1. Dense Semantic Vector Search (VectorSearchEngine)
2. Okapi BM25 Probabilistic Lexical Search (BM25SearchEngine)
3. Reciprocal Rank Fusion (RRF) for optimal ranking:
   RRF(d) = w_vector / (k + rank_vector(d)) + w_bm25 / (k + rank_bm25(d))
4. Jurisdiction & Statutory Section Alignment
"""

import re
import numpy as np
from typing import List, Dict, Any, Optional

from services.vector_search import get_vector_search_engine
from services.bm25_search import get_bm25_search_engine
from services.ingest import get_db_connection
from models.prediction import (
    StructuredCaseProfile,
    CandidateJudgment,
    RankedPrecedent,
    SimilarityBreakdown,
)


class HybridSearchEngine:
    """
    Combines Vector and BM25 rankings using Reciprocal Rank Fusion (RRF).
    """

    def __init__(self, rrf_k: int = 60, vector_weight: float = 0.5, bm25_weight: float = 0.5):
        self.rrf_k = rrf_k
        self.vector_weight = vector_weight
        self.bm25_weight = bm25_weight
        self.vector_engine = get_vector_search_engine()
        self.bm25_engine = get_bm25_search_engine()

    def rank_candidates(
        self,
        profile: StructuredCaseProfile,
        user_description: str,
        candidates: List[CandidateJudgment],
        top_k: int = 5,
    ) -> List[RankedPrecedent]:
        """
        Executes Hybrid RRF ranking across candidate judgments.
        """
        if not candidates:
            return []

        # 1. Fetch full text for candidates from SQLite to build rich representations
        conn = get_db_connection()
        full_texts_map = {}
        try:
            cnrs = [c.cnr for c in candidates]
            placeholders = ",".join(["?"] * len(cnrs))
            rows = conn.execute(
                f"SELECT cnr, full_text FROM judgments WHERE cnr IN ({placeholders})", cnrs
            ).fetchall()
            for r in rows:
                full_texts_map[r["cnr"]] = r["full_text"] or ""
        finally:
            conn.close()

        # 2. Build query text combining narrative description, acts, sections, and issues
        query_parts = [user_description]
        if profile.detected_acts:
            query_parts.append(" ".join(profile.detected_acts))
        if profile.detected_sections:
            query_parts.append(" ".join([f"Section {s}" for s in profile.detected_sections]))
        if profile.legal_issues:
            query_parts.append(" ".join(profile.legal_issues))
        query_text = " ".join(query_parts)

        # 3. Build candidate document representations
        candidate_texts = []
        for c in candidates:
            ft = full_texts_map.get(c.cnr, "")
            # Title + snippet + first 3000 chars of judgment text
            candidate_texts.append(f"{c.title} {c.text_snippet} {ft[:3000]}")

        # 4. Compute Vector Semantic Similarities
        vector_scores = self.vector_engine.compute_semantic_similarities(query_text, candidate_texts)

        # 5. Compute BM25 Lexical Scores
        bm25_scores = self.bm25_engine.compute_bm25_scores(query_text, candidate_texts)

        # 6. Compute Ranks for RRF
        # argsort in descending order gives highest score rank = 1
        vector_ranks = {idx: rank + 1 for rank, idx in enumerate(np.argsort(-vector_scores))}
        bm25_ranks = {idx: rank + 1 for rank, idx in enumerate(np.argsort(-bm25_scores))}

        ranked: List[RankedPrecedent] = []
        query_sec_set = set(profile.detected_sections)
        query_acts_lower = [a.lower() for a in profile.detected_acts]

        for idx, cand in enumerate(candidates):
            v_score = float(vector_scores[idx]) if len(vector_scores) > idx else 0.0
            b_score = float(bm25_scores[idx]) if len(bm25_scores) > idx else 0.0

            v_rank = vector_ranks.get(idx, len(candidates))
            b_rank = bm25_ranks.get(idx, len(candidates))

            # Reciprocal Rank Fusion (RRF) formula
            rrf_score = (self.vector_weight / (self.rrf_k + v_rank)) + (self.bm25_weight / (self.rrf_k + b_rank))

            cand_ft = full_texts_map.get(cand.cnr, "")
            cand_ft_lower = cand_ft.lower()

            # Statutory Section Overlap
            matched_sections = []
            cand_sections = set(cand.matched_sections)
            for sec in query_sec_set:
                if sec in cand_sections or re.search(r"\b" + re.escape(sec) + r"\b", cand_ft, re.IGNORECASE):
                    matched_sections.append(sec)

            sec_boost = min(0.20, len(matched_sections) * 0.10)

            # Act Overlap
            matched_acts = []
            for act in profile.detected_acts:
                act_words = [w.lower() for w in re.findall(r"\b[a-zA-Z]{4,}\b", act) if w.lower() not in {"indian", "code", "procedure", "act"}]
                if any(w in cand_ft_lower for w in act_words):
                    matched_acts.append(act)
            if matched_acts:
                sec_boost = min(0.25, sec_boost + 0.05)

            # Court Jurisdiction Boost
            court_boost = 0.0
            if profile.extracted_court and (
                profile.extracted_court.lower() in cand.court.lower()
                or cand.court.lower() in profile.extracted_court.lower()
            ):
                court_boost = 0.15

            # Combined Normalized Similarity Score [0.02 to 0.98]
            # Blend RRF rank signal (scaled) with direct semantic and lexical scores
            blended_sim = (v_score * 0.40) + (b_score * 0.35) + (rrf_score * self.rrf_k * 0.25) + sec_boost + court_boost

            # Category alignment baseline for valid recognized legal domains
            from services.retrieval import RELATED_CASE_TYPES
            related_types = RELATED_CASE_TYPES.get(profile.case_type, [profile.case_type])
            if profile.case_type != "other" and cand.case_type in related_types:
                category_base = 0.48 if cand.case_type == profile.case_type else 0.40
                blended_sim = max(blended_sim, category_base + (v_score * 0.3) + sec_boost + court_boost)

            final_score = round(min(0.98, max(0.02, blended_sim)), 4)

            breakdown = SimilarityBreakdown(
                semantic_score=round(v_score, 4),
                statutory_boost=round(sec_boost, 4),
                court_match_boost=round(court_boost, 4),
                final_similarity=final_score,
            )

            excerpt = self._extract_relevant_excerpt(cand_ft, matched_sections, cand.title)

            outcome_display = (
                cand.disposal_nature_normalized
                or cand.disposal_nature
                or "disposed"
            ).replace("_", " ").upper()

            ranked.append(
                RankedPrecedent(
                    cnr=cand.cnr,
                    case_name=cand.title,
                    court=cand.court,
                    year=cand.year,
                    decision_date=cand.decision_date,
                    case_type=cand.case_type,
                    outcome=outcome_display,
                    similarity=final_score,
                    score_breakdown=breakdown,
                    matched_sections=sorted(list(set(matched_sections))),
                    matched_acts=sorted(list(set(matched_acts))),
                    excerpt=excerpt,
                    source_url="https://huggingface.co/datasets/overthelex/indian-court-decisions",
                )
            )

        # Sort descending by final similarity score
        ranked.sort(key=lambda x: x.similarity, reverse=True)

        # Filter out weak generic fallbacks when strong matches exist
        strong_matches = [r for r in ranked if r.similarity >= 0.48]
        if len(strong_matches) >= 3:
            return strong_matches[:top_k]

        return ranked[:top_k]

    def _extract_relevant_excerpt(
        self, full_text: str, matched_sections: List[str], title: str
    ) -> str:
        """Extracts the most relevant paragraph mentioning the key sections or holding."""
        if not full_text or len(full_text.strip()) == 0:
            return f"Precedent judgment record for {title}."

        paragraphs = [p.strip() for p in full_text.split("\n") if len(p.strip()) > 60]

        if matched_sections:
            sec = matched_sections[0]
            for p in paragraphs:
                if re.search(r"\b" + re.escape(sec) + r"\b", p, re.IGNORECASE):
                    return p[:300] + ("..." if len(p) > 300 else "")

        if len(paragraphs) >= 2:
            return paragraphs[1][:300] + ("..." if len(paragraphs[1]) > 300 else "")

        return full_text[:300] + ("..." if len(full_text) > 300 else "")


# Singleton
_hybrid_search_engine = None

def get_hybrid_search_engine() -> HybridSearchEngine:
    global _hybrid_search_engine
    if _hybrid_search_engine is None:
        _hybrid_search_engine = HybridSearchEngine()
    return _hybrid_search_engine
