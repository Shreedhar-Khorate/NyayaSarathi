"""
Okapi BM25 Lexical Retrieval Engine for NyayaSarathi.

Implements the BM25 probabilistic relevance ranking algorithm for exact
statutory provision, Act name, section number, and legal term matching.

Formula:
Score(D, Q) = Sum_i IDF(q_i) * (f(q_i, D) * (k1 + 1)) / (f(q_i, D) + k1 * (1 - b + b * (|D| / avgdl)))
where k1 = 1.5, b = 0.75.
"""

import math
import re
from typing import List, Dict, Set
import numpy as np


class BM25SearchEngine:
    """
    Okapi BM25 probabilistic lexical retrieval engine tailored for Indian legal text.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b

    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenizes text preserving legal section numbers, act acronyms, and words.
        """
        if not text:
            return []
        # Extract alphanumeric words and section identifiers
        tokens = re.findall(r"\b[a-zA-Z0-9_\-\.]{2,}\b", text.lower())
        return tokens

    def compute_bm25_scores(
        self,
        query_text: str,
        candidate_texts: List[str],
    ) -> np.ndarray:
        """
        Computes BM25 relevance scores between a query and a set of candidate documents.

        Parameters:
            query_text: User case narrative, acts, and statutory sections.
            candidate_texts: List of candidate judgment text representations.

        Returns:
            1D numpy array of normalized BM25 scores in range [0.0, 1.0].
        """
        if not candidate_texts or not query_text.strip():
            return np.zeros(len(candidate_texts), dtype=float)

        query_tokens = self._tokenize(query_text)
        if not query_tokens:
            return np.zeros(len(candidate_texts), dtype=float)

        N = len(candidate_texts)
        doc_tokens_list = [self._tokenize(doc) for doc in candidate_texts]
        doc_lengths = np.array([len(doc) for doc in doc_tokens_list], dtype=float)
        avgdl = float(np.mean(doc_lengths)) if len(doc_lengths) > 0 and np.mean(doc_lengths) > 0 else 1.0

        # Calculate Document Frequencies (DF) for query tokens
        df: Dict[str, int] = {}
        for q in set(query_tokens):
            df[q] = sum(1 for doc in doc_tokens_list if q in doc)

        # Calculate IDF with standard smoothing: ln((N - df + 0.5) / (df + 0.5) + 1.0)
        idf: Dict[str, float] = {}
        for q, freq in df.items():
            idf[q] = math.log(((N - freq + 0.5) / (freq + 0.5)) + 1.0)

        # Compute raw BM25 scores for each document
        scores = np.zeros(N, dtype=float)
        for idx, doc_tokens in enumerate(doc_tokens_list):
            doc_len = doc_lengths[idx]
            # Term frequencies in this document
            tf_map: Dict[str, int] = {}
            for t in doc_tokens:
                tf_map[t] = tf_map.get(t, 0) + 1

            doc_score = 0.0
            for q in query_tokens:
                if q in tf_map:
                    tf = tf_map[q]
                    numerator = tf * (self.k1 + 1.0)
                    denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / avgdl))
                    doc_score += idf.get(q, 0.0) * (numerator / denominator)

            scores[idx] = max(0.0, doc_score)

        # Min-max normalization to [0.0, 1.0]
        max_s = np.max(scores) if len(scores) > 0 else 0.0
        if max_s > 0:
            scores = scores / max_s

        return scores


# Singleton
_bm25_search_engine = None

def get_bm25_search_engine() -> BM25SearchEngine:
    global _bm25_search_engine
    if _bm25_search_engine is None:
        _bm25_search_engine = BM25SearchEngine()
    return _bm25_search_engine
