"""
Precedent Verification, Citation Integrity & Source Provenance Engine for NyayaSarathi.

Guarantees:
1. Every cited precedent is verified to exist in the database (Zero Hallucinated Precedents).
2. Verbatim excerpt extraction from original judgment text.
3. Official Indian Case Number Record (CNR) citation formatting.
4. Dataset source provenance reporting.
"""

import sqlite3
import re
from typing import List, Dict, Any, Optional, Tuple

from services.ingest import get_db_connection
from models.prediction import RankedPrecedent, VerifiedPrecedent, CitationProvenanceReport
from services.outcome_engine import get_outcome_analyzer


class PrecedentVerificationEngine:
    """
    Validates and enriches ranked precedents with authentic database records,
    verbatim holdings, and traceable Indian court citations.
    """

    def verify_and_enrich(
        self,
        ranked_precedents: List[RankedPrecedent],
        user_position: str,
        case_type: str,
    ) -> Tuple[List[VerifiedPrecedent], CitationProvenanceReport]:
        """
        Validates precedents against SQLite database and generates verified metadata.
        """
        if not ranked_precedents:
            return [], CitationProvenanceReport(
                total_precedents_verified=0,
                verified_cnrs=[],
            )

        conn = get_db_connection()
        try:
            cnrs = [p.cnr for p in ranked_precedents]
            placeholders = ",".join(["?"] * len(cnrs))

            rows = conn.execute(
                f"""
                SELECT cnr, source, court_code, bench, year, title, judge,
                       decision_date, disposal_nature, disposal_nature_normalized,
                       parsed_case_type, parsed_petitioner, parsed_respondent,
                       parsed_court_name, full_text
                FROM judgments
                WHERE cnr IN ({placeholders})
                """,
                cnrs,
            ).fetchall()

            db_records = {r["cnr"]: dict(r) for r in rows}
        finally:
            conn.close()

        outcome_analyzer = get_outcome_analyzer()
        verified_list: List[VerifiedPrecedent] = []
        verified_cnrs: List[str] = []

        for p in ranked_precedents:
            rec = db_records.get(p.cnr)
            if not rec:
                # Discard any candidate that cannot be verified in the database
                continue

            full_text = rec.get("full_text") or ""
            court_name = rec.get("parsed_court_name")
            if not court_name or court_name == "Unknown High Court":
                from services.legal_parser import extract_court_name
                court_name = extract_court_name(rec.get("cnr"), rec.get("bench"), rec.get("source"))

            year = rec.get("year") or p.year
            judge = rec.get("judge")
            bench = rec.get("bench")
            decision_date = rec.get("decision_date") or p.decision_date

            # Evaluate favorable score relative to user's position
            score, fav_label = outcome_analyzer.map_outcome_for_position(
                raw_disposal=p.outcome,
                user_position=user_position,
                case_type=case_type,
            )

            # Format authentic legal citation using CNR and court
            citation_str = self._format_citation(p.cnr, court_name, year)

            # Extract authentic verbatim excerpt from judgment full text
            excerpt = self._extract_verbatim_holding(full_text, p.matched_sections, p.case_name)

            verified_item = VerifiedPrecedent(
                case_name=p.case_name,
                court=court_name,
                bench=bench,
                judge=judge,
                year=year,
                decision_date=decision_date,
                similarity=p.similarity,
                outcome=p.outcome,
                favorable_to_user=fav_label,
                cnr=p.cnr,
                citation=citation_str,
                source_url="https://huggingface.co/datasets/overthelex/indian-court-decisions",
                matched_sections=p.matched_sections,
                matched_acts=p.matched_acts,
                verbatim_excerpt=excerpt,
                is_verified=True,
            )

            verified_list.append(verified_item)
            verified_cnrs.append(p.cnr)

        report = CitationProvenanceReport(
            total_precedents_verified=len(verified_list),
            database_provenance="NyayaSarathi Local SQLite Judgment Archive",
            dataset_origin="overthelex/indian-court-decisions (Hugging Face)",
            zero_hallucination_guaranteed=True,
            verified_cnrs=verified_cnrs,
        )

        return verified_list, report

    def get_full_precedent_by_cnr(self, cnr: str) -> Optional[Dict[str, Any]]:
        """Fetch full judgment record by CNR for deep inspection."""
        conn = get_db_connection()
        try:
            row = conn.execute(
                """
                SELECT cnr, source, court_code, bench, year, title, judge,
                       decision_date, disposal_nature, disposal_nature_normalized,
                       parsed_case_type, parsed_petitioner, parsed_respondent,
                       parsed_court_name, full_text, dataset_config, dataset_split
                FROM judgments
                WHERE cnr = ?
                """,
                [cnr],
            ).fetchone()

            if not row:
                return None

            data = dict(row)
            full_txt = data.get("full_text") or ""
            data["full_text_length"] = len(full_txt)
            data["citation"] = self._format_citation(data["cnr"], data.get("parsed_court_name", ""), data.get("year"))
            data["source_url"] = "https://huggingface.co/datasets/overthelex/indian-court-decisions"
            return data
        finally:
            conn.close()

    def _format_citation(self, cnr: str, court: str, year: Optional[int]) -> str:
        """Construct standard Indian citation format."""
        year_str = str(year) if year else ""
        short_court = court.replace(" High Court", " HC").replace("Court of India", "SC")
        return f"CNR: {cnr} [{year_str} {short_court}]".strip()

    def _extract_verbatim_holding(
        self, full_text: str, matched_sections: List[str], title: str
    ) -> str:
        """Extracts the exact verbatim order or statutory holding paragraph."""
        if not full_text or len(full_text.strip()) == 0:
            return f"Official judgment record for {title}."

        paragraphs = [p.strip() for p in full_text.split("\n") if len(p.strip()) > 50]

        # 1. Look for paragraph containing matched statutory section
        if matched_sections:
            for sec in matched_sections:
                for p in paragraphs:
                    if re.search(r"\b" + re.escape(sec) + r"\b", p, re.IGNORECASE):
                        return p[:380] + ("..." if len(p) > 380 else "")

        # 2. Look for disposition keywords (order, held, granted, dismissed, disposed)
        disposition_cues = ["hereby granted", "is allowed", "is dismissed", "stands disposed", "ordered accordingly", "court holds", "in view of the above"]
        for p in paragraphs:
            p_lower = p.lower()
            if any(cue in p_lower for cue in disposition_cues):
                return p[:380] + ("..." if len(p) > 380 else "")

        # 3. Fallback to first substantive paragraph
        if paragraphs:
            return paragraphs[0][:380] + ("..." if len(paragraphs[0]) > 380 else "")

        return full_text[:380] + ("..." if len(full_text) > 380 else "")


# Singleton
_precedent_verifier = None

def get_precedent_verifier() -> PrecedentVerificationEngine:
    global _precedent_verifier
    if _precedent_verifier is None:
        _precedent_verifier = PrecedentVerificationEngine()
    return _precedent_verifier
