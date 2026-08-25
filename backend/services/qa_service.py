"""
RAG Q&A Service — Wired to Real DB Full-Text Search
Searches the local judgment archive for relevant precedents and
extracts verbatim excerpts as grounded citations.
TODO: Replace with a full vector-store RAG pipeline (Qdrant + LLM).
"""
import re
import os
from typing import List

from schemas.qa import QARequest, QAResponse, Citation
from services.ingest import get_db_connection, DB_PATH


def answer_question(request: QARequest) -> QAResponse:
    """
    Searches local judgment DB for paragraphs relevant to the question.
    Returns grounded answer with verbatim citations from real judgments.
    """
    question = request.question

    # 1. Search DB for relevant judgments
    citations = _search_db_for_citations(question, top_k=3)

    # 2. Synthesize a grounded answer from extracted citations
    if citations:
        evidence_lines = [
            f'"{c.excerpt}" — {c.document}' for c in citations[:2]
        ]
        answer = (
            f"Based on retrieved Indian court judgments, the following precedents are directly "
            f"relevant to your question:\n\n" + "\n\n".join(evidence_lines) +
            "\n\nNote: This is an evidence-grounded summary. Consult a qualified advocate for legal advice."
        )
    else:
        answer = (
            "No closely matching precedents were found in the local judgment archive for your query. "
            "Try rephrasing with specific statutory sections (e.g., 'Section 438 CrPC bail') "
            "or case types (e.g., 'cheque bounce Section 138')."
        )

    return QAResponse(answer=answer, citations=citations)


def _search_db_for_citations(question: str, top_k: int = 3) -> List[Citation]:
    """Search the DB for relevant judgment excerpts and return as Citation objects."""
    if not os.path.exists(DB_PATH):
        return []

    # Extract meaningful keywords from the question
    stop_words = {"the", "and", "for", "this", "that", "with", "from", "under",
                  "what", "how", "when", "who", "why", "does", "can", "should",
                  "into", "upon", "about", "which", "where", "court"}
    keywords = [
        w for w in re.findall(r"\b[a-zA-Z0-9]{3,}\b", question)
        if w.lower() not in stop_words
    ][:5]

    if not keywords:
        return []

    conn = get_db_connection()
    try:
        clauses = ["(full_text LIKE ? OR title LIKE ?)"] * len(keywords)
        params = []
        for kw in keywords:
            params.extend([f"%{kw}%", f"%{kw}%"])

        sql = f"""
            SELECT cnr, title, parsed_court_name, year, full_text
            FROM judgments
            WHERE {" OR ".join(clauses)}
            ORDER BY year DESC
            LIMIT 20
        """
        rows = conn.execute(sql, params).fetchall()
    finally:
        conn.close()

    citations: List[Citation] = []
    seen_docs = set()

    for row in rows:
        title = row["title"] or "Indian Court Judgment"
        if title in seen_docs:
            continue
        seen_docs.add(title)

        full_text = row["full_text"] or ""
        excerpt = _find_best_excerpt(full_text, keywords)
        if not excerpt:
            continue

        court = row["parsed_court_name"] or "High Court"
        year = row["year"] or ""
        doc_label = f"{title} ({court}, {year})"

        # Approximate page number from position in text
        pos = full_text.lower().find(excerpt[:30].lower()) if excerpt else 0
        page = max(1, pos // 2000 + 1)

        citations.append(Citation(
            document=doc_label,
            page=page,
            excerpt=excerpt,
        ))

        if len(citations) >= top_k:
            break

    return citations


def _find_best_excerpt(full_text: str, keywords: List[str], max_len: int = 300) -> str:
    """Find the paragraph that best matches the query keywords."""
    if not full_text:
        return ""

    paragraphs = [p.strip() for p in full_text.split("\n") if len(p.strip()) > 60]
    kw_lower = [k.lower() for k in keywords]

    # Score each paragraph by keyword hits
    best_para = ""
    best_score = 0

    for para in paragraphs:
        para_lower = para.lower()
        score = sum(1 for kw in kw_lower if kw in para_lower)
        if score > best_score:
            best_score = score
            best_para = para

    if best_para and best_score > 0:
        return best_para[:max_len] + ("..." if len(best_para) > max_len else "")

    return ""
