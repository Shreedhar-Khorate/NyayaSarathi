"""
Hybrid Search Service — Wired to Real DB + Vector + BM25 Engine
Searches local SQLite judgment archive using the same hybrid pipeline
as the analyze endpoint (Vector TF-IDF + BM25 + RRF).
"""
import re
import sqlite3
from typing import List

from schemas.search import SearchRequest, SearchResponse, SearchResult
from services.ingest import get_db_connection, DB_PATH
from services.vector_search import get_vector_search_engine
from services.bm25_search import get_bm25_search_engine


def hybrid_search(request: SearchRequest) -> SearchResponse:
    """
    Search the local judgment archive using Vector + BM25 hybrid scoring.
    Returns ranked results with excerpts and source citations.
    """
    import os
    if not os.path.exists(DB_PATH):
        return SearchResponse(results=[])

    query = request.query.strip()
    top_k = max(1, min(request.top_k, 20))

    # --- 1. Fetch candidates from SQLite using keyword filter ---
    conn = get_db_connection()
    try:
        # Extract keywords from query for SQL pre-filter
        keywords = [w for w in re.findall(r"\b[a-zA-Z0-9]{3,}\b", query) if w.lower() not in {
            "the", "and", "for", "this", "that", "with", "from", "under", "into", "upon"
        }]

        if keywords:
            clauses = ["(full_text LIKE ? OR title LIKE ?)"] * min(len(keywords), 4)
            params = []
            for kw in keywords[:4]:
                params.extend([f"%{kw}%", f"%{kw}%"])
            where_sql = " OR ".join(clauses)
            sql = f"""
                SELECT cnr, title, parsed_court_name, year, decision_date,
                       disposal_nature_normalized, full_text
                FROM judgments
                WHERE {where_sql}
                ORDER BY year DESC
                LIMIT 50
            """
            rows = conn.execute(sql, params).fetchall()
        else:
            rows = conn.execute(
                "SELECT cnr, title, parsed_court_name, year, decision_date, disposal_nature_normalized, full_text FROM judgments ORDER BY year DESC LIMIT 50"
            ).fetchall()
    finally:
        conn.close()

    if not rows:
        return SearchResponse(results=[])

    # --- 2. Build text representations ---
    candidates = [dict(r) for r in rows]
    candidate_texts = [
        f"{c['title']} {(c['full_text'] or '')[:2000]}" for c in candidates
    ]

    # --- 3. Compute Vector + BM25 scores ---
    vector_engine = get_vector_search_engine()
    bm25_engine = get_bm25_search_engine()

    v_scores = vector_engine.compute_semantic_similarities(query, candidate_texts)
    b_scores = bm25_engine.compute_bm25_scores(query, candidate_texts)

    # --- 4. Fuse scores (equal weight) ---
    combined = [(v_scores[i] * 0.5) + (b_scores[i] * 0.5) for i in range(len(candidates))]

    # --- 5. Sort and take top_k ---
    ranked = sorted(enumerate(combined), key=lambda x: x[1], reverse=True)[:top_k]

    # --- 6. Build response ---
    results: List[SearchResult] = []
    for idx, score in ranked:
        c = candidates[idx]
        full_text = c.get("full_text") or ""

        # Extract a relevant excerpt
        excerpt = _extract_excerpt(full_text, query)

        court = c.get("parsed_court_name") or "High Court"
        year = c.get("year") or ""
        outcome = (c.get("disposal_nature_normalized") or "disposed").replace("_", " ").title()
        citation = f"{c['title']} [{year} {court}] — {outcome}"

        results.append(SearchResult(
            source_document=c.get("title") or "Indian Court Judgment",
            excerpt=excerpt,
            score=round(float(score), 4),
            citation=citation,
        ))

    return SearchResponse(results=results)


def _extract_excerpt(full_text: str, query: str, max_len: int = 300) -> str:
    """Extract the most relevant paragraph matching the query terms."""
    if not full_text:
        return "No excerpt available."

    keywords = [w.lower() for w in re.findall(r"\b[a-zA-Z]{4,}\b", query)]
    paragraphs = [p.strip() for p in full_text.split("\n") if len(p.strip()) > 60]

    for para in paragraphs:
        para_lower = para.lower()
        if any(kw in para_lower for kw in keywords):
            return para[:max_len] + ("..." if len(para) > max_len else "")

    # Fallback to first substantive paragraph
    if paragraphs:
        return paragraphs[0][:max_len] + ("..." if len(paragraphs[0]) > max_len else "")

    return full_text[:max_len] + ("..." if len(full_text) > max_len else "")
