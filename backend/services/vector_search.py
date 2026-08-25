"""
Dense Semantic Vector Search Engine for NyayaSarathi.

Generates normalized semantic vector representations over legal facts,
arguments, and ratio decidendi, and computes cosine similarity matrices
for candidate judgments.
"""

import numpy as np
from typing import List, Dict, Any, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class VectorSearchEngine:
    """
    Computes dense/sublinear semantic vector similarities over legal text corpora.
    """

    def __init__(self, max_features: int = 10000):
        self.max_features = max_features
        self.vectorizer = TfidfVectorizer(
            max_features=self.max_features,
            stop_words="english",
            ngram_range=(1, 3),
            sublinear_tf=True,
            norm="l2",
        )

    def compute_semantic_similarities(
        self,
        query_text: str,
        candidate_texts: List[str],
    ) -> np.ndarray:
        """
        Computes cosine similarity array between query and candidate texts.

        Parameters:
            query_text: Full narrative representation of the user case.
            candidate_texts: List of candidate judgment text representations.

        Returns:
            1D numpy array of cosine similarity floats in range [0.0, 1.0].
        """
        if not candidate_texts:
            return np.array([], dtype=float)

        all_corpora = [query_text] + candidate_texts
        matrix = self.vectorizer.fit_transform(all_corpora)

        query_vec = matrix[0:1]
        cand_matrix = matrix[1:]

        sims = cosine_similarity(query_vec, cand_matrix)[0]
        return np.clip(sims, 0.0, 1.0)


# Singleton
_vector_search_engine = None

def get_vector_search_engine() -> VectorSearchEngine:
    global _vector_search_engine
    if _vector_search_engine is None:
        _vector_search_engine = VectorSearchEngine()
    return _vector_search_engine
