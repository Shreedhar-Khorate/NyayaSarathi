"""
Dataset Client for Indian Court Decisions (HuggingFace)

Uses DuckDB to query remote Parquet files via HTTP range requests.
This avoids downloading the full 24.8 GB dataset — only the needed
row groups and columns are fetched over the wire.

Dataset: overthelex/indian-court-decisions
License: CC-BY-4.0
"""

import duckdb
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ── Remote Parquet URLs ──────────────────────────────────────────────
# HuggingFace auto-converts datasets to Parquet on refs/convert/parquet branch.
# DuckDB can read these directly via HTTP range requests.

_BASE_URL = (
    "https://huggingface.co/datasets/overthelex/indian-court-decisions"
    "/resolve/refs%2Fconvert%2Fparquet"
)

PARQUET_URLS = {
    "supreme_court": {
        "train": f"{_BASE_URL}/supreme_court/train/0000.parquet",
        "validation": f"{_BASE_URL}/supreme_court/validation/0000.parquet",
        "test": f"{_BASE_URL}/supreme_court/test/0000.parquet",
    },
    "high_courts": {
        "train": f"{_BASE_URL}/high_courts/train/0000.parquet",
        "validation": f"{_BASE_URL}/high_courts/validation/0000.parquet",
        "test": f"{_BASE_URL}/high_courts/test/0000.parquet",
    },
}

# ── Metadata columns (exclude full_text for fast queries) ───────────
METADATA_COLUMNS = [
    "cnr",
    "source",
    "court_code",
    "court_name",
    "bench",
    "year",
    "text_length",
    "title",
    "judge",
    "petitioner",
    "respondent",
    "decision_date",
    "disposal_nature",
    "disposal_nature_normalized",
    "case_type",
]

# All columns including full_text
ALL_COLUMNS = METADATA_COLUMNS + ["full_text"]


class DatasetClient:
    """
    Client for querying the Indian Court Decisions dataset via DuckDB.

    DuckDB reads remote Parquet files using HTTP range requests,
    fetching only the row groups and columns needed for each query.
    No local copy of the dataset is required.
    """

    def __init__(self):
        """Initialize DuckDB with HTTP support for remote Parquet access."""
        self._conn = duckdb.connect(database=":memory:")
        # Install and load the httpfs extension for remote file access
        self._conn.execute("INSTALL httpfs;")
        self._conn.execute("LOAD httpfs;")
        # Optimize DuckDB HTTP range query speed
        self._conn.execute("SET http_timeout=5;")
        self._conn.execute("SET threads=8;")
        self._conn.execute("SET enable_progress_bar=false;")
        self._conn.execute("SET preserve_insertion_order=false;")
        logger.info("DatasetClient initialized with tuned DuckDB + httpfs")

    def _get_parquet_url(
        self, config: str = "supreme_court", split: str = "test"
    ) -> str:
        """Get the remote Parquet URL for a given config and split."""
        if config not in PARQUET_URLS:
            raise ValueError(
                f"Unknown config '{config}'. Available: {list(PARQUET_URLS.keys())}"
            )
        if split not in PARQUET_URLS[config]:
            raise ValueError(
                f"Unknown split '{split}' for config '{config}'. "
                f"Available: {list(PARQUET_URLS[config].keys())}"
            )
        return PARQUET_URLS[config][split]

    def get_record_count(
        self, config: str = "supreme_court", split: str = "test"
    ) -> int:
        """
        Get the total number of records in a config/split.
        This only reads Parquet metadata — no row data is fetched.
        """
        url = self._get_parquet_url(config, split)
        result = self._conn.execute(
            f"SELECT COUNT(*) as total FROM read_parquet('{url}')"
        ).fetchone()
        return result[0] if result else 0

    def get_schema(
        self, config: str = "supreme_court", split: str = "test"
    ) -> List[Dict[str, str]]:
        """
        Get the schema (column names and types) from the Parquet file.
        Reads only file metadata — extremely fast.
        """
        url = self._get_parquet_url(config, split)
        result = self._conn.execute(
            f"DESCRIBE SELECT * FROM read_parquet('{url}')"
        ).fetchall()
        return [
            {"column_name": row[0], "column_type": row[1]}
            for row in result
        ]

    def get_case_type_distribution(
        self,
        config: str = "supreme_court",
        split: str = "test",
        limit: int = 30,
    ) -> List[Dict[str, Any]]:
        """
        Get distribution of case types in the dataset.
        Only reads the case_type column — very efficient.
        """
        url = self._get_parquet_url(config, split)
        result = self._conn.execute(
            f"""
            SELECT
                case_type,
                COUNT(*) as count
            FROM read_parquet('{url}')
            WHERE case_type IS NOT NULL AND case_type != ''
            GROUP BY case_type
            ORDER BY count DESC
            LIMIT {limit}
            """
        ).fetchall()
        return [{"case_type": row[0], "count": row[1]} for row in result]

    def get_outcome_distribution(
        self,
        config: str = "supreme_court",
        split: str = "test",
    ) -> List[Dict[str, Any]]:
        """
        Get distribution of normalized outcomes.
        Only reads the disposal_nature_normalized column.
        """
        url = self._get_parquet_url(config, split)
        result = self._conn.execute(
            f"""
            SELECT
                disposal_nature_normalized,
                COUNT(*) as count
            FROM read_parquet('{url}')
            WHERE disposal_nature_normalized IS NOT NULL
                AND disposal_nature_normalized != ''
            GROUP BY disposal_nature_normalized
            ORDER BY count DESC
            """
        ).fetchall()
        return [{"outcome": row[0], "count": row[1]} for row in result]

    def get_court_distribution(
        self,
        config: str = "supreme_court",
        split: str = "test",
        limit: int = 30,
    ) -> List[Dict[str, Any]]:
        """
        Get distribution of courts in the dataset.
        Only reads the court_name column.
        """
        url = self._get_parquet_url(config, split)
        result = self._conn.execute(
            f"""
            SELECT
                court_name,
                COUNT(*) as count
            FROM read_parquet('{url}')
            WHERE court_name IS NOT NULL AND court_name != ''
            GROUP BY court_name
            ORDER BY count DESC
            LIMIT {limit}
            """
        ).fetchall()
        return [{"court_name": row[0], "count": row[1]} for row in result]

    def get_sample_records(
        self,
        config: str = "supreme_court",
        split: str = "test",
        limit: int = 5,
        include_full_text: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Get sample records from the dataset.
        By default excludes full_text to keep response sizes small.
        """
        url = self._get_parquet_url(config, split)
        columns = ALL_COLUMNS if include_full_text else METADATA_COLUMNS
        cols_str = ", ".join(columns)

        result = self._conn.execute(
            f"""
            SELECT {cols_str}
            FROM read_parquet('{url}')
            LIMIT {limit}
            """
        ).fetchall()

        return [dict(zip(columns, row)) for row in result]

    def query_judgments(
        self,
        config: str = "supreme_court",
        split: str = "test",
        case_type: Optional[str] = None,
        court_name: Optional[str] = None,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        outcome: Optional[str] = None,
        title_contains: Optional[str] = None,
        limit: int = 10,
        include_full_text: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Query judgments with filters.

        All filters use Parquet predicate pushdown where possible,
        meaning DuckDB reads only the matching row groups.

        Parameters:
            case_type: Filter by case_type field (e.g., 'CRL.A', 'WP(C)')
            court_name: Filter where court_name contains this string (case-insensitive)
            year_from: Minimum year (inclusive)
            year_to: Maximum year (inclusive)
            outcome: Filter by disposal_nature_normalized
            title_contains: Filter where title contains this string (case-insensitive)
            limit: Max number of records to return (default 10, max 100)
            include_full_text: Whether to include the full judgment text
        """
        url = self._get_parquet_url(config, split)
        columns = ALL_COLUMNS if include_full_text else METADATA_COLUMNS
        cols_str = ", ".join(columns)

        # Clamp limit
        limit = min(max(1, limit), 100)

        # Build WHERE clauses with parameterized values via f-string
        # (DuckDB doesn't support parameterized queries on remote Parquet easily,
        #  so we sanitize inputs manually)
        conditions = []

        if case_type:
            safe_val = case_type.replace("'", "''")
            conditions.append(f"case_type = '{safe_val}'")

        if court_name:
            safe_val = court_name.replace("'", "''")
            conditions.append(
                f"court_name ILIKE '%{safe_val}%'"
            )

        if year_from is not None:
            conditions.append(f"year >= {int(year_from)}")

        if year_to is not None:
            conditions.append(f"year <= {int(year_to)}")

        if outcome:
            safe_val = outcome.replace("'", "''")
            conditions.append(
                f"disposal_nature_normalized = '{safe_val}'"
            )

        if title_contains:
            safe_val = title_contains.replace("'", "''")
            conditions.append(f"title ILIKE '%{safe_val}%'")

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        query = f"""
            SELECT {cols_str}
            FROM read_parquet('{url}')
            {where_clause}
            LIMIT {limit}
        """

        logger.info(f"Executing remote Parquet query: {query[:200]}...")
        result = self._conn.execute(query).fetchall()

        records = [dict(zip(columns, row)) for row in result]

        # Post-process: convert None values and ensure serializable types
        for record in records:
            for key, value in record.items():
                if value is None:
                    record[key] = None
                elif isinstance(value, (int, float, str, bool)):
                    pass  # Already JSON-serializable
                else:
                    record[key] = str(value)

        return records

    def query_judgments_with_offset(
        self,
        config: str = "supreme_court",
        split: str = "test",
        case_type: Optional[str] = None,
        court_name: Optional[str] = None,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        outcome: Optional[str] = None,
        title_contains: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        include_full_text: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Query judgments with OFFSET pagination for batch ingestion.

        Same as query_judgments but supports offset for walking through
        the dataset in chunks. Used by the ingestion service.
        """
        url = self._get_parquet_url(config, split)
        columns = ALL_COLUMNS if include_full_text else METADATA_COLUMNS
        cols_str = ", ".join(columns)

        limit = min(max(1, limit), 100)
        offset = max(0, offset)

        conditions = []

        if case_type:
            safe_val = case_type.replace("'", "''")
            conditions.append(f"case_type = '{safe_val}'")

        if court_name:
            safe_val = court_name.replace("'", "''")
            conditions.append(f"court_name ILIKE '%{safe_val}%'")

        if year_from is not None:
            conditions.append(f"year >= {int(year_from)}")

        if year_to is not None:
            conditions.append(f"year <= {int(year_to)}")

        if outcome:
            safe_val = outcome.replace("'", "''")
            conditions.append(f"disposal_nature_normalized = '{safe_val}'")

        if title_contains:
            safe_val = title_contains.replace("'", "''")
            conditions.append(f"title ILIKE '%{safe_val}%'")

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        query = f"""
            SELECT {cols_str}
            FROM read_parquet('{url}')
            {where_clause}
            LIMIT {limit}
            OFFSET {offset}
        """

        logger.info(f"Remote query offset={offset} limit={limit}")
        result = self._conn.execute(query).fetchall()

        records = [dict(zip(columns, row)) for row in result]

        for record in records:
            for key, value in record.items():
                if value is None:
                    record[key] = None
                elif isinstance(value, (int, float, str, bool)):
                    pass
                else:
                    record[key] = str(value)

        return records

    def close(self):
        """Close the DuckDB connection."""
        self._conn.close()
        logger.info("DatasetClient connection closed")


# ── Module-level singleton ──────────────────────────────────────────
# Reuse a single DuckDB connection across requests to benefit from
# Parquet metadata caching.

_client: Optional[DatasetClient] = None


def get_dataset_client() -> DatasetClient:
    """Get or create the singleton DatasetClient instance."""
    global _client
    if _client is None:
        _client = DatasetClient()
    return _client
