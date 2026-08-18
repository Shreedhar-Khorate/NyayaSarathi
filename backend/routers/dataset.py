"""
Dataset exploration and ingestion API router.

Provides endpoints to:
- Verify remote dataset access and inspect schema (Stage 1)
- Selectively ingest judgments into local SQLite (Stage 2)
- Query the local judgment database (Stage 2)
"""

from fastapi import APIRouter, Query, BackgroundTasks
from typing import Optional
from services.dataset_client import get_dataset_client
from services.ingest import ingest_judgments, get_db_stats, search_local_judgments

router = APIRouter(prefix="/api/dataset", tags=["dataset"])


@router.get("/health")
def dataset_health():
    """
    Verify that the remote dataset is accessible.
    Returns basic connectivity status and record count.
    """
    try:
        client = get_dataset_client()
        count = client.get_record_count(config="supreme_court", split="test")
        return {
            "status": "ok",
            "message": "Remote dataset is accessible via DuckDB + httpfs",
            "supreme_court_test_records": count,
            "dataset": "overthelex/indian-court-decisions",
            "method": "DuckDB remote Parquet (HTTP range requests)",
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to access remote dataset: {str(e)}",
        }


@router.get("/schema")
def dataset_schema(
    config: str = Query("supreme_court", description="Dataset config: supreme_court or high_courts"),
    split: str = Query("test", description="Dataset split: train, validation, or test"),
):
    """
    Get the schema of the remote Parquet dataset.
    This reads only file metadata — no row data is transferred.
    """
    client = get_dataset_client()
    schema = client.get_schema(config=config, split=split)
    count = client.get_record_count(config=config, split=split)
    return {
        "config": config,
        "split": split,
        "record_count": count,
        "columns": schema,
    }


@router.get("/stats/case-types")
def case_type_stats(
    config: str = Query("supreme_court"),
    split: str = Query("test"),
    limit: int = Query(30, ge=1, le=100),
):
    """
    Get the distribution of case types in the dataset.
    Only reads the case_type column — efficient single-column scan.
    """
    client = get_dataset_client()
    distribution = client.get_case_type_distribution(config=config, split=split, limit=limit)
    return {
        "config": config,
        "split": split,
        "case_type_distribution": distribution,
        "total_types": len(distribution),
    }


@router.get("/stats/outcomes")
def outcome_stats(
    config: str = Query("supreme_court"),
    split: str = Query("test"),
):
    """
    Get the distribution of normalized outcomes (disposal_nature_normalized).
    """
    client = get_dataset_client()
    distribution = client.get_outcome_distribution(config=config, split=split)
    return {
        "config": config,
        "split": split,
        "outcome_distribution": distribution,
    }


@router.get("/stats/courts")
def court_stats(
    config: str = Query("supreme_court"),
    split: str = Query("test"),
    limit: int = Query(30, ge=1, le=100),
):
    """
    Get the distribution of courts in the dataset.
    """
    client = get_dataset_client()
    distribution = client.get_court_distribution(config=config, split=split, limit=limit)
    return {
        "config": config,
        "split": split,
        "court_distribution": distribution,
    }


@router.get("/sample")
def sample_records(
    config: str = Query("supreme_court"),
    split: str = Query("test"),
    limit: int = Query(5, ge=1, le=20),
    include_full_text: bool = Query(False, description="Include full judgment text (large)"),
):
    """
    Get sample records from the dataset.
    By default excludes full_text to keep response sizes small.
    """
    client = get_dataset_client()
    records = client.get_sample_records(
        config=config, split=split, limit=limit, include_full_text=include_full_text
    )
    return {
        "config": config,
        "split": split,
        "count": len(records),
        "records": records,
    }


@router.get("/query")
def query_judgments(
    config: str = Query("supreme_court"),
    split: str = Query("test"),
    case_type: Optional[str] = Query(None, description="Filter by case_type (e.g., CRL.A, WP(C))"),
    court_name: Optional[str] = Query(None, description="Filter where court_name contains this string"),
    year_from: Optional[int] = Query(None, description="Minimum year (inclusive)"),
    year_to: Optional[int] = Query(None, description="Maximum year (inclusive)"),
    outcome: Optional[str] = Query(None, description="Filter by disposal_nature_normalized"),
    title_contains: Optional[str] = Query(None, description="Filter where title contains this string"),
    limit: int = Query(10, ge=1, le=100),
    include_full_text: bool = Query(False),
):
    """
    Query judgments with filters.

    Filters are pushed down to Parquet row groups where possible,
    so only matching data is transferred over the network.

    Example queries:
    - /api/dataset/query?case_type=CRL.A&limit=5
    - /api/dataset/query?outcome=allowed&year_from=2020
    - /api/dataset/query?title_contains=bail&limit=10
    """
    client = get_dataset_client()
    records = client.query_judgments(
        config=config,
        split=split,
        case_type=case_type,
        court_name=court_name,
        year_from=year_from,
        year_to=year_to,
        outcome=outcome,
        title_contains=title_contains,
        limit=limit,
        include_full_text=include_full_text,
    )
    return {
        "config": config,
        "split": split,
        "filters": {
            "case_type": case_type,
            "court_name": court_name,
            "year_from": year_from,
            "year_to": year_to,
            "outcome": outcome,
            "title_contains": title_contains,
        },
        "count": len(records),
        "records": records,
    }


# ════════════════════════════════════════════════════════════════════
# STAGE 2: Selective Ingestion & Local Database
# ════════════════════════════════════════════════════════════════════

@router.post("/ingest")
def ingest(
    config: str = Query("high_courts"),
    split: str = Query("test"),
    outcome: Optional[str] = Query(None, description="Filter by outcome (e.g., bail_granted, dismissed, allowed)"),
    year_from: Optional[int] = Query(None),
    year_to: Optional[int] = Query(None),
    title_contains: Optional[str] = Query(None),
    batch_size: int = Query(100, ge=10, le=100),
    max_records: int = Query(500, ge=10, le=5000),
    include_full_text: bool = Query(True),
):
    """
    Selectively ingest judgments from remote dataset into local SQLite.

    Downloads records in batches, enriches each with legal_parser
    (extracts case type, parties, court name from title/CNR),
    and stores in the local database.

    Example ingestion commands:
    - Bail cases: POST /ingest?outcome=bail_granted&max_records=500
    - Recent dismissed: POST /ingest?outcome=dismissed&year_from=2020&max_records=300
    - All outcomes 2023+: POST /ingest?year_from=2023&max_records=1000
    """
    result = ingest_judgments(
        config=config,
        split=split,
        outcome=outcome,
        year_from=year_from,
        year_to=year_to,
        title_contains=title_contains,
        batch_size=batch_size,
        max_records=max_records,
        include_full_text=include_full_text,
    )
    return result


@router.post("/ingest/seed")
def seed_database(
    max_per_outcome: int = Query(200, ge=50, le=1000, description="Max records per outcome category"),
):
    """
    Seed the local database with a balanced set of judgments across
    all major outcome categories. This is the recommended initial
    ingestion to build a diverse local dataset for prediction.

    Ingests from high_courts/test split (1.4M records available).
    Covers: allowed, dismissed, disposed, bail_granted, bail_rejected,
            partly_allowed, quashed, withdrawn.
    """
    outcomes = [
        "allowed",
        "dismissed",
        "disposed",
        "bail_granted",
        "bail_rejected",
        "partly_allowed",
        "quashed",
        "withdrawn",
    ]

    results = []
    total_inserted = 0

    for outcome in outcomes:
        try:
            result = ingest_judgments(
                config="high_courts",
                split="test",
                outcome=outcome,
                year_from=2015,
                batch_size=100,
                max_records=max_per_outcome,
                include_full_text=True,
            )
            results.append({
                "outcome": outcome,
                "status": result["status"],
                "fetched": result["records_fetched"],
                "inserted": result["records_inserted"],
                "skipped": result["records_skipped"],
                "elapsed": result["elapsed_seconds"],
            })
            total_inserted += result["records_inserted"]
        except Exception as e:
            results.append({
                "outcome": outcome,
                "status": "error",
                "error": str(e),
            })

    return {
        "status": "completed",
        "total_inserted": total_inserted,
        "outcome_results": results,
    }


@router.get("/local/stats")
def local_db_stats():
    """
    Get statistics about the local judgment database.
    Shows record counts, distributions, and ingestion history.
    """
    return get_db_stats()


@router.get("/local/search")
def local_search(
    case_type: Optional[str] = Query(None, description="Filter by parsed case type (e.g., bail, writ_civil, criminal_appeal)"),
    outcome: Optional[str] = Query(None, description="Filter by disposal_nature_normalized"),
    court: Optional[str] = Query(None, description="Filter by court name (partial match)"),
    year_from: Optional[int] = Query(None),
    year_to: Optional[int] = Query(None),
    title_contains: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
):
    """
    Search the local judgment database.
    Much faster than remote queries — uses local SQLite indexes.
    """
    records = search_local_judgments(
        case_type=case_type,
        outcome=outcome,
        court=court,
        year_from=year_from,
        year_to=year_to,
        title_contains=title_contains,
        limit=limit,
    )
    return {
        "source": "local_database",
        "count": len(records),
        "records": records,
    }
