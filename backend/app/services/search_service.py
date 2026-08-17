"""
Hybrid Search Service — Sample Implementation
TODO: Replace with real Qdrant + Elasticsearch + RRF fusion.
"""
from app.schemas.search import SearchRequest, SearchResponse, SearchResult


def hybrid_search(request: SearchRequest) -> SearchResponse:
    # Sample static results — replace with real vector + BM25 retrieval
    sample_results = [
        SearchResult(
            source_document="State of Maharashtra vs. Praful Desai (2003)",
            excerpt=(
                "The court held that electronic evidence is admissible subject to "
                "fulfilment of conditions under Section 65B of the Indian Evidence Act."
            ),
            score=0.91,
            citation="AIR 2003 SC 2053, Para 14",
        ),
        SearchResult(
            source_document="Shafhi Mohammad vs. State of Himachal Pradesh (2018)",
            excerpt=(
                "Secondary evidence in electronic form is admissible without the 65B "
                "certificate when the device is not in the party's possession."
            ),
            score=0.84,
            citation="(2018) 2 SCC 801, Para 21",
        ),
    ]

    return SearchResponse(results=sample_results[: request.top_k])
