"""
Hybrid Similarity Ranking Engine for NyayaSarathi.

Uses HybridSearchEngine (Dense Vector Search + Okapi BM25 + Reciprocal Rank Fusion / RRF)
to rank candidate Indian court judgments with statutory, act, and jurisdiction alignment.
"""

from typing import List
from models.prediction import StructuredCaseProfile, CandidateJudgment, RankedPrecedent
from services.hybrid_search import get_hybrid_search_engine, HybridSearchEngine


class HybridSimilarityRanker:
    """
    Ranks candidate Indian court judgments using Vector + BM25 Reciprocal Rank Fusion (RRF).
    """

    def __init__(self):
        self._engine = get_hybrid_search_engine()

    def rank_candidates(
        self,
        profile: StructuredCaseProfile,
        user_description: str,
        candidates: List[CandidateJudgment],
        top_k: int = 5,
    ) -> List[RankedPrecedent]:
        """
        Ranks candidate judgments using Hybrid Vector + BM25 RRF scoring.
        """
        return self._engine.rank_candidates(
            profile=profile,
            user_description=user_description,
            candidates=candidates,
            top_k=top_k,
        )


# Singleton
_ranker = None

def get_hybrid_similarity_ranker() -> HybridSimilarityRanker:
    global _ranker
    if _ranker is None:
        _ranker = HybridSimilarityRanker()
    return _ranker

# Backward compatibility alias
get_similarity_ranker = get_hybrid_similarity_ranker
SimilarityRanker = HybridSimilarityRanker
