"""
Judgment Ingestion Service for NyayaSarathi.

Selectively ingests judgments from the remote HuggingFace dataset into
a local SQLite database. Enriches raw records with parsed metadata
(case type, parties, court name) using legal_parser.

DESIGN PRINCIPLES:
- Never download the entire 24.8 GB dataset
- Ingest only what we need: specific outcomes, year ranges, courts
- Enrich records with legal_parser metadata extraction
- Store locally for fast retrieval, future vector indexing
- Idempotent: re-running won't create duplicates (CNR is unique key)
"""

import sqlite3
import os
import logging
import time
from typing import Any, Dict, List, Optional

from services.dataset_client import get_dataset_client
from services.legal_parser import parse_title, normalize_case_type, extract_court_name

logger = logging.getLogger(__name__)

# ── Database path ────────────────────────────────────────────────────
DB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
DB_PATH = os.path.join(DB_DIR, "nyayasarathi.db")


def _ensure_db_dir():
    """Create the data directory if it doesn't exist."""
    os.makedirs(DB_DIR, exist_ok=True)


def get_db_connection() -> sqlite3.Connection:
    """Get a connection to the local SQLite database."""
    _ensure_db_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_database():
    """
    Initialize the SQLite database schema.

    The judgments table stores enriched records with both raw dataset
    fields and parsed metadata from legal_parser.
    """
    conn = get_db_connection()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS judgments (
                -- Primary key: CNR is the unique case identifier
                cnr TEXT PRIMARY KEY,

                -- Raw fields from HuggingFace dataset
                source TEXT,              -- 'sc' or 'hc'
                court_code TEXT,
                bench TEXT,
                year INTEGER,
                text_length INTEGER,
                title TEXT,
                judge TEXT,
                decision_date TEXT,
                disposal_nature TEXT,      -- Raw outcome string
                disposal_nature_normalized TEXT,  -- Normalized outcome label

                -- Full judgment text (stored separately for efficiency)
                full_text TEXT,

                -- ── Enriched fields (from legal_parser) ──────────
                -- These are extracted/derived from title + cnr
                parsed_case_type_raw TEXT,     -- Raw case type from title (e.g., "CR. MISC.")
                parsed_case_type TEXT,         -- Normalized category (e.g., "bail")
                parsed_petitioner TEXT,
                parsed_respondent TEXT,
                parsed_court_name TEXT,        -- Court name from CNR prefix

                -- ── Metadata ─────────────────────────────────────
                ingested_at TEXT DEFAULT (datetime('now')),
                dataset_config TEXT,      -- 'supreme_court' or 'high_courts'
                dataset_split TEXT        -- 'train', 'validation', 'test'
            );

            -- Indexes for efficient filtering
            CREATE INDEX IF NOT EXISTS idx_judgments_year
                ON judgments(year);
            CREATE INDEX IF NOT EXISTS idx_judgments_outcome
                ON judgments(disposal_nature_normalized);
            CREATE INDEX IF NOT EXISTS idx_judgments_case_type
                ON judgments(parsed_case_type);
            CREATE INDEX IF NOT EXISTS idx_judgments_court
                ON judgments(parsed_court_name);
            CREATE INDEX IF NOT EXISTS idx_judgments_source
                ON judgments(source);
            CREATE INDEX IF NOT EXISTS idx_judgments_date
                ON judgments(decision_date);

            -- Composite indexes for common query patterns
            CREATE INDEX IF NOT EXISTS idx_judgments_type_outcome
                ON judgments(parsed_case_type, disposal_nature_normalized);
            CREATE INDEX IF NOT EXISTS idx_judgments_court_outcome
                ON judgments(parsed_court_name, disposal_nature_normalized);

            -- Ingestion tracking
            CREATE TABLE IF NOT EXISTS ingestion_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at TEXT DEFAULT (datetime('now')),
                completed_at TEXT,
                config TEXT,
                split TEXT,
                filters TEXT,
                records_fetched INTEGER DEFAULT 0,
                records_inserted INTEGER DEFAULT 0,
                records_skipped INTEGER DEFAULT 0,
                status TEXT DEFAULT 'running',
                error TEXT
            );
        """)
        conn.commit()
        logger.info("Database schema initialized successfully")
    finally:
        conn.close()


def _enrich_record(record: Dict[str, Any], config: str, split: str) -> Dict[str, Any]:
    """
    Enrich a raw dataset record with parsed metadata.

    Uses legal_parser to extract:
    - Case type from title
    - Petitioner/respondent from title
    - Court name from CNR prefix + bench code
    """
    title = record.get("title", "") or ""
    cnr = record.get("cnr", "") or ""
    bench = record.get("bench", "") or ""
    source = record.get("source", "") or ""

    # Parse title for case type and parties
    parsed = parse_title(title)

    # Normalize case type
    case_type_normalized = normalize_case_type(parsed.get("case_type_raw"))

    # Extract court name from CNR/bench/source
    court_name = extract_court_name(cnr, bench, source)

    return {
        "cnr": cnr,
        "source": source,
        "court_code": record.get("court_code", ""),
        "bench": bench,
        "year": record.get("year"),
        "text_length": record.get("text_length"),
        "title": title,
        "judge": record.get("judge", ""),
        "decision_date": record.get("decision_date", ""),
        "disposal_nature": record.get("disposal_nature", ""),
        "disposal_nature_normalized": record.get("disposal_nature_normalized", ""),
        "full_text": record.get("full_text", ""),
        # Enriched fields
        "parsed_case_type_raw": parsed.get("case_type_raw", ""),
        "parsed_case_type": case_type_normalized,
        "parsed_petitioner": parsed.get("petitioner", ""),
        "parsed_respondent": parsed.get("respondent", ""),
        "parsed_court_name": court_name,
        # Tracking
        "dataset_config": config,
        "dataset_split": split,
    }


def _insert_records(conn: sqlite3.Connection, records: List[Dict[str, Any]]) -> tuple:
    """
    Insert enriched records into the database.
    Uses INSERT OR IGNORE to skip duplicates (by CNR).
    Returns (inserted_count, skipped_count).
    """
    inserted = 0
    skipped = 0

    for rec in records:
        try:
            conn.execute("""
                INSERT OR IGNORE INTO judgments (
                    cnr, source, court_code, bench, year, text_length,
                    title, judge, decision_date,
                    disposal_nature, disposal_nature_normalized,
                    full_text,
                    parsed_case_type_raw, parsed_case_type,
                    parsed_petitioner, parsed_respondent,
                    parsed_court_name,
                    dataset_config, dataset_split
                ) VALUES (
                    :cnr, :source, :court_code, :bench, :year, :text_length,
                    :title, :judge, :decision_date,
                    :disposal_nature, :disposal_nature_normalized,
                    :full_text,
                    :parsed_case_type_raw, :parsed_case_type,
                    :parsed_petitioner, :parsed_respondent,
                    :parsed_court_name,
                    :dataset_config, :dataset_split
                )
            """, rec)

            if conn.total_changes > 0:
                inserted += 1
            else:
                skipped += 1
        except Exception as e:
            logger.warning(f"Failed to insert record {rec.get('cnr')}: {e}")
            skipped += 1

    return inserted, skipped


def ingest_judgments(
    config: str = "high_courts",
    split: str = "test",
    outcome: Optional[str] = None,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    title_contains: Optional[str] = None,
    batch_size: int = 100,
    max_records: int = 500,
    include_full_text: bool = True,
) -> Dict[str, Any]:
    """
    Selectively ingest judgments from the remote dataset into local SQLite.

    This fetches records in batches, enriches them with legal_parser,
    and stores them locally. Uses DuckDB OFFSET/LIMIT for pagination.

    Parameters:
        config: 'supreme_court' or 'high_courts'
        split: 'train', 'validation', or 'test'
        outcome: Filter by disposal_nature_normalized
        year_from: Minimum year (inclusive)
        year_to: Maximum year (inclusive)
        title_contains: Filter where title contains this string
        batch_size: Records per remote query (max 100)
        max_records: Total records to ingest in this run
        include_full_text: Whether to fetch full judgment text

    Returns:
        Summary dict with ingestion statistics.
    """
    init_database()

    conn = get_db_connection()
    client = get_dataset_client()

    # Log the ingestion run
    filters_desc = f"outcome={outcome}, year={year_from}-{year_to}, title={title_contains}"
    cursor = conn.execute(
        "INSERT INTO ingestion_log (config, split, filters) VALUES (?, ?, ?)",
        (config, split, filters_desc)
    )
    log_id = cursor.lastrowid
    conn.commit()

    total_fetched = 0
    total_inserted = 0
    total_skipped = 0
    start_time = time.time()

    batch_size = min(batch_size, 100)

    try:
        offset = 0
        while total_fetched < max_records:
            remaining = max_records - total_fetched
            current_batch = min(batch_size, remaining)

            # Fetch batch from remote dataset via DuckDB
            records = client.query_judgments_with_offset(
                config=config,
                split=split,
                outcome=outcome,
                year_from=year_from,
                year_to=year_to,
                title_contains=title_contains,
                limit=current_batch,
                offset=offset,
                include_full_text=include_full_text,
            )

            if not records:
                logger.info(f"No more records at offset {offset}. Ingestion complete.")
                break

            # Enrich with legal_parser
            enriched = [_enrich_record(r, config, split) for r in records]

            # Insert into local DB
            inserted, skipped = _insert_records(conn, enriched)
            conn.commit()

            total_fetched += len(records)
            total_inserted += inserted
            total_skipped += skipped
            offset += len(records)

            logger.info(
                f"Batch: fetched={len(records)}, inserted={inserted}, "
                f"skipped={skipped}. Total: {total_fetched}/{max_records}"
            )

        elapsed = round(time.time() - start_time, 2)

        # Update ingestion log
        conn.execute("""
            UPDATE ingestion_log
            SET completed_at = datetime('now'),
                records_fetched = ?,
                records_inserted = ?,
                records_skipped = ?,
                status = 'completed'
            WHERE id = ?
        """, (total_fetched, total_inserted, total_skipped, log_id))
        conn.commit()

        result = {
            "status": "completed",
            "config": config,
            "split": split,
            "filters": {
                "outcome": outcome,
                "year_from": year_from,
                "year_to": year_to,
                "title_contains": title_contains,
            },
            "records_fetched": total_fetched,
            "records_inserted": total_inserted,
            "records_skipped": total_skipped,
            "elapsed_seconds": elapsed,
            "database_path": DB_PATH,
        }

        logger.info(f"Ingestion complete: {result}")
        return result

    except Exception as e:
        conn.execute("""
            UPDATE ingestion_log
            SET completed_at = datetime('now'),
                records_fetched = ?,
                records_inserted = ?,
                records_skipped = ?,
                status = 'error',
                error = ?
            WHERE id = ?
        """, (total_fetched, total_inserted, total_skipped, str(e), log_id))
        conn.commit()
        logger.error(f"Ingestion failed: {e}")
        raise
    finally:
        conn.close()


def get_db_stats() -> Dict[str, Any]:
    """Get statistics about the local judgment database."""
    if not os.path.exists(DB_PATH):
        return {"status": "not_initialized", "total_records": 0}

    conn = get_db_connection()
    try:
        total = conn.execute("SELECT COUNT(*) FROM judgments").fetchone()[0]

        # Outcome distribution
        outcomes = conn.execute("""
            SELECT disposal_nature_normalized, COUNT(*) as count
            FROM judgments
            WHERE disposal_nature_normalized IS NOT NULL
                AND disposal_nature_normalized != ''
            GROUP BY disposal_nature_normalized
            ORDER BY count DESC
        """).fetchall()

        # Case type distribution
        case_types = conn.execute("""
            SELECT parsed_case_type, COUNT(*) as count
            FROM judgments
            WHERE parsed_case_type IS NOT NULL
                AND parsed_case_type != ''
                AND parsed_case_type != 'other'
            GROUP BY parsed_case_type
            ORDER BY count DESC
            LIMIT 20
        """).fetchall()

        # Court distribution
        courts = conn.execute("""
            SELECT parsed_court_name, COUNT(*) as count
            FROM judgments
            WHERE parsed_court_name IS NOT NULL
                AND parsed_court_name != ''
            GROUP BY parsed_court_name
            ORDER BY count DESC
            LIMIT 20
        """).fetchall()

        # Year range
        year_range = conn.execute("""
            SELECT MIN(year), MAX(year) FROM judgments
        """).fetchone()

        # Ingestion history
        ingestions = conn.execute("""
            SELECT * FROM ingestion_log
            ORDER BY id DESC LIMIT 5
        """).fetchall()

        db_size_mb = round(os.path.getsize(DB_PATH) / (1024 * 1024), 2)

        return {
            "status": "initialized",
            "total_records": total,
            "database_size_mb": db_size_mb,
            "year_range": {
                "min": year_range[0] if year_range else None,
                "max": year_range[1] if year_range else None,
            },
            "outcome_distribution": [
                {"outcome": r[0], "count": r[1]} for r in outcomes
            ],
            "case_type_distribution": [
                {"case_type": r[0], "count": r[1]} for r in case_types
            ],
            "court_distribution": [
                {"court": r[0], "count": r[1]} for r in courts
            ],
            "recent_ingestions": [
                dict(r) for r in ingestions
            ],
        }
    finally:
        conn.close()


def search_local_judgments(
    case_type: Optional[str] = None,
    outcome: Optional[str] = None,
    court: Optional[str] = None,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    title_contains: Optional[str] = None,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """
    Search the local judgment database with filters.
    This is fast since it queries the local SQLite, not the remote dataset.
    """
    if not os.path.exists(DB_PATH):
        return []

    conn = get_db_connection()
    try:
        conditions = []
        params = []

        if case_type:
            conditions.append("parsed_case_type = ?")
            params.append(case_type)

        if outcome:
            conditions.append("disposal_nature_normalized = ?")
            params.append(outcome)

        if court:
            conditions.append("parsed_court_name LIKE ?")
            params.append(f"%{court}%")

        if year_from:
            conditions.append("year >= ?")
            params.append(year_from)

        if year_to:
            conditions.append("year <= ?")
            params.append(year_to)

        if title_contains:
            conditions.append("title LIKE ?")
            params.append(f"%{title_contains}%")

        where = ""
        if conditions:
            where = "WHERE " + " AND ".join(conditions)

        limit = min(max(1, limit), 100)
        params.append(limit)

        rows = conn.execute(f"""
            SELECT cnr, source, title, judge, year, decision_date,
                   disposal_nature, disposal_nature_normalized,
                   parsed_case_type_raw, parsed_case_type,
                   parsed_petitioner, parsed_respondent,
                   parsed_court_name, text_length
            FROM judgments
            {where}
            ORDER BY year DESC, decision_date DESC
            LIMIT ?
        """, params).fetchall()

        return [dict(r) for r in rows]
    finally:
        conn.close()
