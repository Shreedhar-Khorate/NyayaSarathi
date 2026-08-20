"""
Candidate Judgment Retrieval Engine.

Implements multi-tiered retrieval from local indexed SQLite database:
Tier 1: Exact Case Type & Statutory Sections Overlap
Tier 2: Same Legal Category & Forum Matching
Tier 3: Key Fact & Domain FTS Keyword Search
Tier 4: Broad Domain Precedent Fallback
"""

import sqlite3
import re
import logging
from typing import List, Dict, Any, Optional, Set

from models.prediction import StructuredCaseProfile, CandidateJudgment, CandidateRetrievalResponse
from services.ingest import get_db_connection

logger = logging.getLogger(__name__)

# Legal Domain to Related Category Taxonomy Mapping
RELATED_CASE_TYPES: Dict[str, List[str]] = {
    "bail": ["bail", "criminal_appeal", "criminal_revision", "writ_criminal", "other"],
    "criminal": ["criminal_appeal", "criminal_revision", "bail", "writ_criminal", "other"],
    "writ_civil": ["writ_civil", "pil", "service", "civil_appeal", "other"],
    "writ_criminal": ["writ_criminal", "bail", "criminal_appeal", "other"],
    "contract": ["commercial", "civil", "civil_appeal", "contract", "other"],
    "cheque_bounce": ["commercial", "criminal_appeal", "criminal_revision", "civil", "other"],
    "civil": ["civil", "civil_appeal", "commercial", "property", "other"],
    "civil_appeal": ["civil_appeal", "civil", "appeal", "other"],
    "property": ["property", "civil", "civil_appeal", "writ_civil", "other"],
    "family": ["family", "civil_appeal", "criminal_revision", "other"],
    "motor_accident": ["motor_accident", "appeal", "civil_appeal", "other"],
    "service": ["writ_civil", "appeal", "civil", "other"],
    "tax": ["tax", "commercial", "writ_civil", "other"],
    "arbitration": ["commercial", "civil_appeal", "civil", "other"],
    "consumer": ["consumer", "civil_appeal", "writ_civil", "other"],
    "contempt": ["contempt", "writ_civil", "other"],
    "constitutional": ["writ_civil", "pil", "civil_appeal", "other"],
}


class CandidateRetrievalEngine:
    """
    Tiered candidate retriever matching Indian judgments by statutory provisions,
    case taxonomy, court forum, and factual keywords.
    """

    def retrieve_candidates(
        self,
        profile: StructuredCaseProfile,
        min_candidates: int = 15,
        max_candidates: int = 50,
    ) -> CandidateRetrievalResponse:
        """
        Execute multi-tier retrieval strategy to collect candidate judgments.
        """
        conn = get_db_connection()
        collected_cnrs: Set[str] = set()
        candidates: List[CandidateJudgment] = []
        tiers_used: List[str] = []

        try:
            # ── Priority 0: Live Remote Hugging Face Search if requested Court is not in Local DB ──
            court_in_db = True
            is_specialized_tribunal = any(t in (profile.extracted_court or "").lower() for t in ["ncdrc", "nclt", "ngt", "cat", "rera", "itat", "consumer", "tribunal"])
            if profile.extracted_court:
                court_in_db = bool(conn.execute("SELECT 1 FROM judgments WHERE parsed_court_name LIKE ? LIMIT 1", [f"%{profile.extracted_court}%"]).fetchone())

            if profile.extracted_court and not court_in_db and not is_specialized_tribunal:
                t0_remote = self._tier4_live_remote_fallback(
                    conn, profile, max_count=10, exclude_cnrs=collected_cnrs
                )
                for r in t0_remote:
                    if r.cnr not in collected_cnrs:
                        collected_cnrs.add(r.cnr)
                        candidates.append(r)
                if t0_remote:
                    tiers_used.append("Tier 0 (Live Remote HuggingFace Search)")

            # ── Tier 1: Exact Case Type / Related + Statutory Sections Overlap ──
            t1_results = []
            if profile.detected_sections:
                t1_results = self._tier1_statutory_retrieval(conn, profile, max_count=30)
                for r in t1_results:
                    if r.cnr not in collected_cnrs:
                        collected_cnrs.add(r.cnr)
                        candidates.append(r)
                if t1_results:
                    tiers_used.append("Tier 1 (Exact Statutory & Case Type Match)")

            # ── Level 3: DuckDuckGo Public Legal Authority Discovery ─────────
            # Triggered for specialized tribunals (NCDRC, NCLT, etc.) or when exact section matches in local DB are low (< 3)
            if is_specialized_tribunal or len(candidates) < 3 or (profile.case_type in {"consumer", "cyber_crime", "arbitration"} and len(candidates) < 5):
                try:
                    from services.duckduckgo_search import get_duckduckgo_search_engine
                    ddg_engine = get_duckduckgo_search_engine()
                    ddg_results = ddg_engine.search_public_judgments(profile, max_results=5)
                    for r in ddg_results:
                        if r.cnr not in collected_cnrs:
                            collected_cnrs.add(r.cnr)
                            candidates.append(r)
                    if ddg_results:
                        tiers_used.append("Level 3 (DuckDuckGo Public Legal Authority Discovery)")
                except Exception as e:
                    logger.debug(f"DuckDuckGo search notice: {e}")

            # ── Tier 2: Exact Case Type + Related Category Match ────────────
            if len(candidates) < max_candidates:
                remaining = max_candidates - len(candidates)
                t2_results = self._tier2_category_court_retrieval(
                    conn, profile, max_count=remaining, exclude_cnrs=collected_cnrs
                )
                for r in t2_results:
                    if r.cnr not in collected_cnrs:
                        collected_cnrs.add(r.cnr)
                        candidates.append(r)
                if t2_results:
                    tiers_used.append("Tier 2 (Category & Jurisdiction Match)")

            # ── Tier 3: Key Fact & Keyword FTS Match ────────────────────────
            if len(candidates) < min_candidates:
                remaining = max_candidates - len(candidates)
                t3_results = self._tier3_keyword_retrieval(
                    conn, profile, max_count=remaining, exclude_cnrs=collected_cnrs
                )
                for r in t3_results:
                    if r.cnr not in collected_cnrs:
                        collected_cnrs.add(r.cnr)
                        candidates.append(r)
                if t3_results:
                    tiers_used.append("Tier 3 (Factual Keyword & Domain Match)")

            # ── Tier 4: Automatic Live Remote Hugging Face Fallback ──────────
            if len(candidates) < min_candidates:
                remaining = max_candidates - len(candidates)
                t4_remote = self._tier4_live_remote_fallback(
                    conn, profile, max_count=remaining, exclude_cnrs=collected_cnrs
                )
                for r in t4_remote:
                    if r.cnr not in collected_cnrs:
                        collected_cnrs.add(r.cnr)
                        candidates.append(r)
                if t4_remote:
                    tiers_used.append("Tier 4 (Live Remote HuggingFace Search)")

            # ── Tier 5: Broad Domain Fallback ────────────────────────────────
            if len(candidates) < min_candidates:
                remaining = min_candidates - len(candidates)
                t5_results = self._tier5_broad_fallback(
                    conn, profile, max_count=remaining, exclude_cnrs=collected_cnrs
                )
                for r in t5_results:
                    if r.cnr not in collected_cnrs:
                        collected_cnrs.add(r.cnr)
                        candidates.append(r)
                if t5_results:
                    tiers_used.append("Tier 5 (Broad Precedent Fallback)")

            query_summary = {
                "case_type": profile.case_type,
                "sections_searched": profile.detected_sections,
                "acts_searched": profile.detected_acts,
                "court_filtered": profile.extracted_court,
            }

            return CandidateRetrievalResponse(
                status="success",
                query_summary=query_summary,
                total_candidates_found=len(candidates),
                retrieval_tiers_used=tiers_used,
                candidates=candidates,
            )

        finally:
            conn.close()

    def _tier1_statutory_retrieval(
        self,
        conn: sqlite3.Connection,
        profile: StructuredCaseProfile,
        max_count: int,
    ) -> List[CandidateJudgment]:
        """Match by statutory sections in full_text/title and related case types."""
        if not profile.detected_sections:
            return []

        candidates = []
        sec_clauses = []
        params = []

        for sec in profile.detected_sections[:4]:
            sec_clauses.append("(full_text LIKE ? OR title LIKE ?)")
            params.extend([f"%{sec}%", f"%{sec}%"])

        sec_sql = " OR ".join(sec_clauses)
        related = RELATED_CASE_TYPES.get(profile.case_type, [profile.case_type])
        placeholders = ",".join("?" for _ in related)
        params.extend(related)

        court_clause = ""
        if profile.extracted_court:
            court_clause = "AND (parsed_court_name LIKE ? OR parsed_court_name = 'High Court')"
            params.append(f"%{profile.extracted_court}%")

        query = f"""
            SELECT cnr, title, judge, year, decision_date,
                   disposal_nature, disposal_nature_normalized,
                   parsed_case_type, parsed_petitioner, parsed_respondent,
                   parsed_court_name, full_text
            FROM judgments
            WHERE ({sec_sql})
              AND parsed_case_type IN ({placeholders})
              {court_clause}
            ORDER BY year DESC
            LIMIT ?
        """
        params.append(max_count)

        rows = conn.execute(query, params).fetchall()
        for r in rows:
            dict_row = dict(r)
            matched = self._find_matched_sections(dict_row.get("full_text", ""), profile.detected_sections)
            candidates.append(self._row_to_candidate(dict_row, "Tier 1", matched))

        return candidates

    def _tier2_category_court_retrieval(
        self,
        conn: sqlite3.Connection,
        profile: StructuredCaseProfile,
        max_count: int,
        exclude_cnrs: Set[str],
    ) -> List[CandidateJudgment]:
        """Match by case taxonomy category and court hierarchy."""
        related = RELATED_CASE_TYPES.get(profile.case_type, [profile.case_type])
        placeholders = ",".join("?" for _ in related)
        params: List[Any] = list(related)

        court_clause = ""
        if profile.extracted_court:
            court_clause = "AND (parsed_court_name LIKE ? OR parsed_court_name = 'High Court')"
            params.append(f"%{profile.extracted_court}%")

        candidates = []

        query = f"""
            SELECT cnr, title, judge, year, decision_date,
                   disposal_nature, disposal_nature_normalized,
                   parsed_case_type, parsed_petitioner, parsed_respondent,
                   parsed_court_name, full_text
            FROM judgments
            WHERE parsed_case_type IN ({placeholders}) {court_clause}
            ORDER BY year DESC
            LIMIT ?
        """
        params.append(max_count + len(exclude_cnrs))

        rows = conn.execute(query, params).fetchall()
        for r in rows:
            dict_row = dict(r)
            if dict_row["cnr"] not in exclude_cnrs:
                matched = self._find_matched_sections(dict_row.get("full_text", ""), profile.detected_sections)
                candidates.append(self._row_to_candidate(dict_row, "Tier 2", matched))
                if len(candidates) >= max_count:
                    break

        return candidates

    def _tier3_keyword_retrieval(
        self,
        conn: sqlite3.Connection,
        profile: StructuredCaseProfile,
        max_count: int,
        exclude_cnrs: Set[str],
    ) -> List[CandidateJudgment]:
        """Match by keywords from key facts or legal issues."""
        keywords = []
        for f in profile.key_facts + profile.legal_issues:
            words = [w for w in re.findall(r"\b[a-zA-Z]{4,}\b", f) if w.lower() not in {"this", "that", "with", "from", "have", "been", "court", "order"}]
            keywords.extend(words[:3])

        if not keywords:
            return []

        kw_clauses = []
        params = []
        for kw in keywords[:5]:
            kw_clauses.append("(full_text LIKE ? OR title LIKE ?)")
            params.extend([f"%{kw}%", f"%{kw}%"])

        where_kw = " OR ".join(kw_clauses)
        params.append(max_count + len(exclude_cnrs))

        query = f"""
            SELECT cnr, title, judge, year, decision_date,
                   disposal_nature, disposal_nature_normalized,
                   parsed_case_type, parsed_petitioner, parsed_respondent,
                   parsed_court_name, full_text
            FROM judgments
            WHERE {where_kw}
            ORDER BY year DESC
            LIMIT ?
        """
        rows = conn.execute(query, params).fetchall()
        candidates = []
        for r in rows:
            dict_row = dict(r)
            if dict_row["cnr"] not in exclude_cnrs:
                matched = self._find_matched_sections(dict_row.get("full_text", ""), profile.detected_sections)
                candidates.append(self._row_to_candidate(dict_row, "Tier 3", matched))
                if len(candidates) >= max_count:
                    break

        return candidates

    def _tier4_live_remote_fallback(
        self,
        conn: sqlite3.Connection,
        profile: StructuredCaseProfile,
        max_count: int,
        exclude_cnrs: Set[str],
    ) -> List[CandidateJudgment]:
        """
        Live remote DuckDB query against Hugging Face dataset if local DB needs expansion.
        Enriches and stores retrieved records in local SQLite for future instant runs.
        """
        try:
            from services.dataset_client import get_dataset_client
            from services.ingest import _enrich_record

            client = get_dataset_client()
            court_str = (profile.extracted_court or "").lower()
            if "supreme" in court_str:
                config = "supreme_court"
            else:
                config = "high_courts"

            # Pull remote records via ultra-fast metadata-only DuckDB range query (<50KB, <1s)
            remote_rows = client.query_judgments(
                config=config,
                split="test",
                case_type=None,
                court_name=None,
                limit=min(max_count, 6),
                include_full_text=False,
            )

            new_candidates = []
            for rec in remote_rows:
                cnr_val = rec.get("cnr")
                if cnr_val and cnr_val not in exclude_cnrs:
                    enriched = _enrich_record(rec, config, "test")
                    # Cache to local SQLite
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
                    """, enriched)
                    conn.commit()

                    matched = self._find_matched_sections(enriched.get("full_text", ""), profile.detected_sections)
                    new_candidates.append(self._row_to_candidate(enriched, "Tier 4 (Live Remote HuggingFace)", matched))
                    exclude_cnrs.add(cnr_val)
                    if len(new_candidates) >= max_count:
                        break
            return new_candidates
        except Exception as e:
            logger.warning(f"Live remote HuggingFace fallback skipped: {e}")
            return []

    def _tier5_broad_fallback(
        self,
        conn: sqlite3.Connection,
        profile: StructuredCaseProfile,
        max_count: int,
        exclude_cnrs: Set[str],
    ) -> List[CandidateJudgment]:
        """Broad fallback when strict matches are exhausted."""
        query = """
            SELECT cnr, title, judge, year, decision_date,
                   disposal_nature, disposal_nature_normalized,
                   parsed_case_type, parsed_petitioner, parsed_respondent,
                   parsed_court_name, full_text
            FROM judgments
            ORDER BY year DESC
            LIMIT ?
        """
        rows = conn.execute(query, [max_count + len(exclude_cnrs)]).fetchall()
        candidates = []
        for r in rows:
            dict_row = dict(r)
            if dict_row["cnr"] not in exclude_cnrs:
                matched = self._find_matched_sections(dict_row.get("full_text", ""), profile.detected_sections)
                candidates.append(self._row_to_candidate(dict_row, "Tier 5", matched))
                if len(candidates) >= max_count:
                    break
        return candidates

    def _find_matched_sections(self, full_text: str, query_sections: List[str]) -> List[str]:
        """Find which statutory sections from query are mentioned in judgment text."""
        if not full_text or not query_sections:
            return []
        matched = []
        full_upper = full_text.upper()
        for sec in query_sections:
            if re.search(r"\b" + re.escape(sec) + r"\b", full_upper):
                matched.append(sec)
        return matched

    def _row_to_candidate(
        self,
        row: Dict[str, Any],
        tier: str,
        matched_sections: List[str],
    ) -> CandidateJudgment:
        """Convert database row dictionary to CandidateJudgment schema."""
        petitioner = row.get("parsed_petitioner") or "Petitioner"
        respondent = row.get("parsed_respondent") or "Respondent"
        title = row.get("title") or f"{petitioner} Vs {respondent}"
        full_txt = row.get("full_text") or ""
        snippet = full_txt[:350].strip() if full_txt else f"Judgment of {title}"

        return CandidateJudgment(
            cnr=row.get("cnr") or "CNR_UNKNOWN",
            title=title,
            court=row.get("parsed_court_name") or "High Court",
            year=row.get("year"),
            decision_date=row.get("decision_date"),
            case_type=row.get("parsed_case_type") or "other",
            disposal_nature=row.get("disposal_nature"),
            disposal_nature_normalized=row.get("disposal_nature_normalized"),
            matched_sections=matched_sections,
            text_snippet=snippet,
            retrieval_tier=tier,
        )


# Singleton
_candidate_retrieval_engine = None

def get_candidate_retrieval_engine() -> CandidateRetrievalEngine:
    global _candidate_retrieval_engine
    if _candidate_retrieval_engine is None:
        _candidate_retrieval_engine = CandidateRetrievalEngine()
    return _candidate_retrieval_engine
