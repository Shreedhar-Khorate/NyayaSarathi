"""
Hybrid Similarity Ranking Engine for NyayaSarathi.

Combines:
1. TF-IDF N-gram semantic cosine similarity across legal text representations.
2. Exact statutory overlap boost (Section & Act alignment).
3. Forum / High Court jurisdiction alignment boost.
4. Transparent score attribution (SimilarityBreakdown).
"""

import sqlite3
import re
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from services.ingest import get_db_connection
from models.prediction import (
    StructuredCaseProfile,
    CandidateJudgment,
    RankedPrecedent,
    SimilarityBreakdown,
)


class HybridSimilarityRanker:
    """
    Ranks candidate Indian court judgments against a structured case profile.
    """

    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=6000,
            stop_words="english",
            ngram_range=(1, 2),
            sublinear_tf=True,
        )

    def rank_candidates(
        self,
        profile: StructuredCaseProfile,
        user_description: str,
        candidates: List[CandidateJudgment],
        top_k: int = 5,
    ) -> List[RankedPrecedent]:
        """
        Ranks candidate judgments using hybrid semantic + statutory scoring.
        """
        if not candidates:
            return []

        # Load full text for candidates from SQLite to build comprehensive corpus
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

        # Build query text combining user description, explicit acts, and sections
        query_parts = [user_description]
        if profile.detected_acts:
            query_parts.append(" ".join(profile.detected_acts))
        if profile.detected_sections:
            query_parts.append(" ".join([f"Section {s}" for s in profile.detected_sections]))
        if profile.legal_issues:
            query_parts.append(" ".join(profile.legal_issues))

        query_corpus = " ".join(query_parts)

        # Build candidate corpora
        candidate_corpora = []
        for c in candidates:
            ft = full_texts_map.get(c.cnr, "")
            # Use title + snippet + first 2500 chars of full text for rich representation
            corpus = f"{c.title} {c.text_snippet} {ft[:2500]}"
            candidate_corpora.append(corpus)

        # Vectorize
        all_texts = [query_corpus] + candidate_corpora
        tfidf_matrix = self.vectorizer.fit_transform(all_texts)

        query_vec = tfidf_matrix[0:1]
        cand_vecs = tfidf_matrix[1:]

        # Raw semantic cosine similarities
        raw_sims = cosine_similarity(query_vec, cand_vecs)[0]

        ranked: List[RankedPrecedent] = []

        query_sec_set = set(profile.detected_sections)
        query_acts_lower = [a.lower() for a in profile.detected_acts]

        for idx, cand in enumerate(candidates):
            semantic_score = float(raw_sims[idx])
            cand_ft = full_texts_map.get(cand.cnr, "")
            cand_ft_lower = cand_ft.lower()

            # 1. Statutory Section Overlap Boost
            matched_sections = []
            cand_sections = set(cand.matched_sections)
            for sec in query_sec_set:
                if sec in cand_sections or re.search(r"\b" + re.escape(sec) + r"\b", cand_ft, re.IGNORECASE):
                    matched_sections.append(sec)

            sec_overlap_count = len(matched_sections)
            statutory_boost = min(0.25, sec_overlap_count * 0.12)

            # 2. Act Overlap Boost
            matched_acts = []
            for act in profile.detected_acts:
                # check keywords from act name
                act_words = [w.lower() for w in re.findall(r"\b[a-zA-Z]{4,}\b", act) if w.lower() not in {"indian", "code", "procedure", "act"}]
                if any(w in cand_ft_lower for w in act_words):
                    matched_acts.append(act)

            if matched_acts:
                statutory_boost = min(0.30, statutory_boost + 0.08)

            # 3. Court / Forum Match Boost
            court_boost = 0.0
            if profile.extracted_court and (
                profile.extracted_court.lower() in cand.court.lower()
                or cand.court.lower() in profile.extracted_court.lower()
            ):
                court_boost = 0.20

            # 4. Final Similarity Calculation
            final_score = min(0.98, semantic_score + statutory_boost + court_boost)

            # Category alignment bonus for valid recognized legal domains (not 'other')
            from services.retrieval import RELATED_CASE_TYPES
            related_types = RELATED_CASE_TYPES.get(profile.case_type, [profile.case_type])
            if profile.case_type != "other" and cand.case_type in related_types:
                category_base = 0.48 if cand.case_type == profile.case_type else 0.40
                final_score = max(final_score, min(0.98, category_base + (semantic_score * 0.5) + statutory_boost + court_boost))

            final_score = round(min(0.98, max(0.02, final_score)), 4)

            breakdown = SimilarityBreakdown(
                semantic_score=round(semantic_score, 4),
                statutory_boost=round(statutory_boost, 4),
                court_match_boost=round(court_boost, 4),
                final_similarity=final_score,
            )

            # Generate concise excerpt
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

        # If we have high-matching precedents (>= 0.48), filter out weak generic fallbacks
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

        # Try to find paragraph matching the first section
        if matched_sections:
            sec = matched_sections[0]
            for p in paragraphs:
                if re.search(r"\b" + re.escape(sec) + r"\b", p, re.IGNORECASE):
                    return p[:300] + ("..." if len(p) > 300 else "")

        # Fallback to first non-empty descriptive paragraph
        if paragraphs:
            return paragraphs[0][:300] + ("..." if len(paragraphs[0]) > 300 else "")

        return full_text[:300] + ("..." if len(full_text) > 300 else "")


# Singleton
_similarity_ranker = None

def get_similarity_ranker() -> HybridSimilarityRanker:
    global _similarity_ranker
    if _similarity_ranker is None:
        _similarity_ranker = HybridSimilarityRanker()
    return _similarity_ranker
