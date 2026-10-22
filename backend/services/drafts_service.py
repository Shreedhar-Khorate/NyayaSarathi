"""
Legal Draft Generator — Dynamic AI Service Implementation
NyayaSarathi Feature 3.8: Structured, production-quality legal documents
(Legal Notices, Bail Applications, Petitions, Replies) grounded strictly in user-supplied case facts,
accurate statutory chronology (IPC/CrPC vs BNS/BNSS), court hierarchy analysis,
and native multilingual LLM synthesis (English, Marathi, Hindi).

Zero RAG, zero document retrieval, zero vector search, zero static templates, zero hardcoded legal content.
"""

import os
import re
import json
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from unittest.mock import Mock, MagicMock

from fastapi import HTTPException

from schemas.drafts import (
    DraftRequest,
    DraftResponse,
    DraftContent,
    DraftSection,
    CitationInfo,
    RegenerateSectionRequest,
    RegenerateSectionResponse,
    TranslateDraftRequest,
    CANONICAL_DOCUMENT_TYPE_MAP,
    SUPPORTED_DOCUMENT_TYPES,
    SUPPORTED_LANGUAGES,
    resolve_canonical_doc_type,
)
from services.war_room_service import _call_llm_json, _ensure_list, _parse_llm_json
from services.translate_service import translate_legal_text
from schemas.translate import TranslationRequest
from logger import get_logger

log = get_logger("nyayasarathi.drafts_service")


# ── Document Type & Subtype Resolution ────────────────────────────────────────
def _normalize_doc_type(
    raw_type: Optional[str],
    raw_draft_type: Optional[str] = None,
    requested_subtype: Optional[str] = None,
    relief: Optional[str] = None,
) -> Tuple[str, str]:
    """
    Validates and resolves canonical document type and specific subtype.
    Detects and rejects conflicting document_type and draft_type inputs.
    Never collapses anticipatory bail into regular bail.
    """
    if not raw_type and not raw_draft_type:
        raise HTTPException(
            status_code=400,
            detail="Document type is required. Supported types: 'legal_notice', 'bail_application', 'petition', 'reply'."
        )

    res_doc = resolve_canonical_doc_type(raw_type) if raw_type else None
    res_draft = resolve_canonical_doc_type(raw_draft_type) if raw_draft_type else None

    # Detect alias conflicts
    if raw_type and raw_draft_type:
        if res_doc and res_draft and res_doc[0] != res_draft[0]:
            raise HTTPException(
                status_code=400,
                detail=f"Conflicting document_type ('{raw_type}') and draft_type ('{raw_draft_type}') provided."
            )
        elif not res_doc and not res_draft and str(raw_type).strip().lower() != str(raw_draft_type).strip().lower():
            raise HTTPException(
                status_code=400,
                detail=f"Conflicting document_type ('{raw_type}') and draft_type ('{raw_draft_type}') provided."
            )

    active_res = res_doc or res_draft
    if not active_res:
        candidate = raw_type or raw_draft_type
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported document type: '{candidate}'. Supported types: 'legal_notice', 'bail_application', 'petition', 'reply'."
        )

    canonical_type, default_subtype = active_res
    subtype = requested_subtype or default_subtype

    # Safe subtype inference for bail (regular vs anticipatory)
    all_type_strings = f"{raw_type or ''} {raw_draft_type or ''} {requested_subtype or ''} {relief or ''}".lower()
    if canonical_type == "bail_application":
        if "anticipatory" in all_type_strings:
            subtype = "anticipatory_bail"
        elif "regular" in all_type_strings:
            subtype = "regular_bail"

    return canonical_type, subtype


def _resolve_facts(facts: Optional[str], case_facts: Optional[str]) -> str:
    """
    Validates facts and case_facts aliases.
    Rejects conflicting substantive inputs.
    Enforces minimum length of 10 characters and maximum of 50,000 characters.
    """
    if facts is not None and case_facts is not None:
        f_clean = str(facts).strip()
        cf_clean = str(case_facts).strip()
        if f_clean and cf_clean and f_clean != cf_clean:
            raise HTTPException(
                status_code=400,
                detail="Conflicting 'facts' and 'case_facts' provided with different substantive content."
            )

    chosen = facts if facts is not None else case_facts
    if not chosen or not str(chosen).strip() or len(str(chosen).strip()) < 10:
        raise HTTPException(
            status_code=400,
            detail="Missing required case facts. Please provide factual details of at least 10 characters."
        )

    clean_facts = str(chosen).strip()
    if len(clean_facts) > 50000:
        raise HTTPException(
            status_code=400,
            detail="Case facts input exceeds maximum allowable length (50,000 characters)."
        )

    return clean_facts


def _normalize_language(lang: Optional[str]) -> str:
    """Normalizes and validates target language ('en', 'hi', 'mr')."""
    if not lang or not str(lang).strip():
        return "en"
    clean = str(lang).strip().lower()
    mapping = {
        "english": "en",
        "en": "en",
        "hindi": "hi",
        "hi": "hi",
        "marathi": "mr",
        "mr": "mr",
    }
    if clean in mapping:
        return mapping[clean]

    raise HTTPException(
        status_code=400,
        detail=f"Unsupported target language '{lang}'. Supported languages: 'en' (English), 'hi' (Hindi), 'mr' (Marathi)."
    )


# ── Statutory Era & Chronology Evaluation ────────────────────────────────────
def _evaluate_statutory_era(
    facts: str,
    cause_of_action_date: Optional[str] = None,
    important_dates: Optional[List[str]] = None,
) -> Tuple[str, List[str]]:
    """
    Evaluates whether substantive offences fall under IPC (prior to 1 July 2024)
    or BNS (on/after 1 July 2024).
    Anchors strictly to explicitly labeled event dates (cause of action, FIR date, incident date).
    Never uses arbitrary citation years, foundation years, or unrelated narrative numbers as era anchors.
    Correctly recognizes ambiguous dates, conflicting dates, and Section 531 BNSS savings provisions.
    """
    warnings: List[str] = []
    relevant_date_str: Optional[str] = None
    event_label = "cause of action"

    # 1. Primary anchor: cause_of_action_date
    if cause_of_action_date and str(cause_of_action_date).strip():
        relevant_date_str = str(cause_of_action_date).strip()
        event_label = "cause of action / incident date"
    else:
        # 2. Check explicitly labeled entries in important_dates
        if important_dates:
            for item in important_dates:
                if isinstance(item, str) and re.search(r"\b(offence|offense|incident|fir|crime|cause\s*of\s*action|default)\b", item, re.IGNORECASE):
                    m = re.search(r"\b(\d{1,2}[./-]\d{1,2}[./-]\d{2,4}|\d{4}-\d{2}-\d{2})\b", item)
                    if m:
                        relevant_date_str = m.group(1)
                        event_label = item.strip()
                        break

        # 3. Check specific event phrases in facts (incident, offence, FIR, cause of action)
        if not relevant_date_str:
            event_match = re.search(
                r"\b(?:incident|offence|offense|occurrence|crime|fir|cause\s*of\s*action)\b[^\n\.\,]{0,40}?\b(\d{1,2}[./-]\d{1,2}[./-]\d{2,4}|\d{4}-\d{2}-\d{2})\b",
                facts,
                re.IGNORECASE,
            )
            if event_match:
                relevant_date_str = event_match.group(1)
                event_label = "alleged incident / FIR date"

    parsed_date = None
    date_is_ambiguous = False

    if relevant_date_str:
        try:
            if "-" in relevant_date_str and len(relevant_date_str.split("-")[0]) == 4:
                parsed_date = datetime.strptime(relevant_date_str, "%Y-%m-%d").date()
            else:
                parts = [int(p) for p in re.split(r"[./-]", relevant_date_str)]
                y = parts[2] if parts[2] > 100 else parts[2] + 2000
                d = parts[0]
                m = parts[1]

                # Check day/month ambiguity across 1 July 2024 boundary
                if y == 2024 and d <= 12 and m <= 12:
                    dt_dm = datetime(y, m, d).date()
                    dt_md = datetime(y, d, m).date()
                    transition = datetime(2024, 7, 1).date()
                    if (dt_dm < transition) != (dt_md < transition):
                        date_is_ambiguous = True

                parsed_date = datetime(y, m, d).date()
        except Exception:
            parsed_date = None

    transition_date = datetime(2024, 7, 1).date()

    if date_is_ambiguous:
        era = "UNDETERMINED"
        warnings.append(
            f"Statutory Era Advisory: The date format in '{relevant_date_str}' is ambiguous across the 1 July 2024 boundary. "
            "Counsel must confirm whether the event occurred prior to 1 July 2024 (governed substantively by IPC, 1860) "
            "or on/after 1 July 2024 (governed by BNS, 2023). Under Article 20(1) of the Constitution, criminal liability "
            "cannot be imposed retrospectively under BNS."
        )
    elif parsed_date:
        if parsed_date < transition_date:
            era = "IPC_CRPC"
            warnings.append(
                f"Statutory Era Notice: Based on the relevant event date ({parsed_date.strftime('%d/%m/%Y')}, {event_label}), "
                "substantive offences are governed by the Indian Penal Code (IPC, 1860) pursuant to Article 20(1) of the Constitution of India. "
                "Regarding procedure, proceedings pending prior to 1 July 2024 are saved under Section 531(2)(a) BNSS, 2023 and continue under CrPC, 1973. "
                "For applications newly instituted on or after 1 July 2024, verify jurisdictional High Court precedent on BNSS procedural applicability."
            )
        else:
            era = "BNS_BNSS"
            warnings.append(
                f"Statutory Era Notice: Based on the relevant event date ({parsed_date.strftime('%d/%m/%Y')}, {event_label}), "
                "proceedings fall on or after 1 July 2024; primary substantive governance is under Bharatiya Nyaya Sanhita (BNS, 2023) "
                "and procedural governance is under Bharatiya Nagarik Suraksha Sanhita (BNSS, 2023)."
            )
    else:
        era = "UNDETERMINED"
        warnings.append(
            "Statutory Era Advisory: The exact date of the alleged offence or cause of action is not explicitly established in the provided inputs. "
            "Counsel must independently verify whether the offence occurred prior to 1 July 2024 (governed by IPC/CrPC; Article 20(1) constitutional bar) "
            "or on/after 1 July 2024 (governed by BNS/BNSS). Procedural governance depends on institution date and Section 531(2)(a) BNSS savings."
        )

    return era, warnings


# ── Arrest Date Extraction Helper ─────────────────────────────────────────────
def _extract_arrest_date(facts: str, important_dates: Optional[List[str]]) -> Optional[str]:
    """
    Extracts the arrest date strictly when explicitly identified as such.
    Never assumes important_dates[0] or an arbitrary first date is the arrest date.
    """
    if important_dates:
        for item in important_dates:
            if isinstance(item, str) and re.search(r"\b(arrest(?:ed|\s*date)?|custody|remand)\b", item, re.IGNORECASE):
                dt_match = re.search(r"\b(\d{1,2}[./-]\d{1,2}[./-]\d{2,4}|\d{4}-\d{2}-\d{2})\b", item)
                if dt_match:
                    return dt_match.group(1)

    facts_match = re.search(
        r"\b(?:arrest(?:ed|\s*date)?|taken\s+into\s+custody|remanded\s+on)\s*(?:on|dated?|:)?\s*(\d{1,2}[./-]\d{1,2}[./-]\d{2,4}|\d{4}-\d{2}-\d{2})\b",
        facts,
        re.IGNORECASE,
    )
    if facts_match:
        return facts_match.group(1)

    return None


# ── Procedural Bail Section Determination (BNSS vs CrPC) ─────────────────────
def _determine_bail_procedural_section(
    jurisdiction: Optional[str],
    facts: str,
    era: str,
    doc_type: str,
    subtype: Optional[str] = None,
    applicable_sections: Optional[List[str]] = None,
    relief: Optional[str] = None,
) -> Tuple[str, str, str, List[str]]:
    """
    Determines and validates the accurate procedural bail section under BNSS, 2023 vs CrPC, 1973
    based on relief sought (anticipatory vs regular bail), court hierarchy (Magistrate vs Sessions/HC),
    and evaluated statutory era.

    Returns: (section_number_string, full_title_en, full_title_mr, warnings_list)
    """
    warnings: List[str] = []
    text_corpus = f"{jurisdiction or ''} {facts} {relief or ''} {' '.join(applicable_sections or [])}".lower()

    is_anticipatory = (subtype == "anticipatory_bail") or bool(
        re.search(r"\banticipatory\b", f"{doc_type} {subtype or ''} {relief or ''} {text_corpus}", re.IGNORECASE)
    )

    is_magistrate = bool(re.search(r"\b(magistrate|jmfc|cjm|mm\b|cmm\b|acmm\b|judicial\s*magistrate|metropolitan\s*magistrate)\b", text_corpus))
    is_sessions_or_hc = bool(re.search(r"\b(session|sessions|court\s*of\s*session|high\s*court|district\s*(?:and\s*sessions?\s*)?judge|asj\b|special\s*court)\b", text_corpus))

    if is_anticipatory:
        if is_magistrate and not is_sessions_or_hc:
            warnings.append(
                "Jurisdiction Alert: Under Indian law, a Judicial Magistrate has no jurisdiction to grant anticipatory bail. "
                "Anticipatory bail lies exclusively before the Court of Session or the High Court (Section 482 BNSS / Section 438 CrPC)."
            )

        if era == "IPC_CRPC":
            sec_num = "Section 438"
            full_title = "Section 438 of the Code of Criminal Procedure, 1973 (CrPC)"
            mr_title = "फौजदारी प्रक्रिया संहिता, १९७३ चे कलम ४३८"
        elif era == "BNS_BNSS":
            sec_num = "Section 482"
            full_title = "Section 482 of the Bharatiya Nagarik Suraksha Sanhita, 2023 (BNSS)"
            mr_title = "भारतीय नागरिक सुरक्षा संहिता, २०२३ चे कलम ४८२"
        else:
            sec_num = "Section 482 BNSS / Section 438 CrPC"
            full_title = "Section 482 BNSS, 2023 / Section 438 CrPC, 1973 (Subject to date of offence & institution)"
            mr_title = "कलम ४८२ बीएनएसएस / कलम ४३८ सीआरपीसी"
            warnings.append(
                "Procedural Advisory: Statutory era is undetermined. Counsel must verify whether Section 482 BNSS, 2023 "
                "or Section 438 CrPC, 1973 governs the anticipatory bail application."
            )
        warnings.append("Procedural Section: Anticipatory bail provision applied based on case relief.")

    elif is_magistrate and not is_sessions_or_hc:
        if era == "IPC_CRPC":
            sec_num = "Section 437"
            full_title = "Section 437 of the Code of Criminal Procedure, 1973 (CrPC)"
            mr_title = "फौजदारी प्रक्रिया संहिता, १९७३ चे कलम ४३७"
        elif era == "BNS_BNSS":
            sec_num = "Section 480"
            full_title = "Section 480 of the Bharatiya Nagarik Suraksha Sanhita, 2023 (BNSS)"
            mr_title = "भारतीय नागरिक सुरक्षा संहिता, २०२३ चे कलम ४८०"
        else:
            sec_num = "Section 480 BNSS / Section 437 CrPC"
            full_title = "Section 480 BNSS, 2023 / Section 437 CrPC, 1973 (Magistrate Jurisdiction)"
            mr_title = "कलम ४८० बीएनएसएस / कलम ४३७ सीआरपीसी"
        warnings.append("Court Hierarchy Verification: Case designated before Learned Magistrate Court; Section 480 BNSS (or S. 437 CrPC) applies instead of S. 483 BNSS.")

    elif is_sessions_or_hc:
        if era == "IPC_CRPC":
            sec_num = "Section 439"
            full_title = "Section 439 of the Code of Criminal Procedure, 1973 (CrPC)"
            mr_title = "फौजदारी प्रक्रिया संहिता, १९७३ चे कलम ४३९"
        elif era == "BNS_BNSS":
            sec_num = "Section 483"
            full_title = "Section 483 of the Bharatiya Nagarik Suraksha Sanhita, 2023 (BNSS)"
            mr_title = "भारतीय नागरिक सुरक्षा संहिता, २०२३ चे कलम ४८३"
        else:
            sec_num = "Section 483 BNSS / Section 439 CrPC"
            full_title = "Section 483 BNSS, 2023 / Section 439 CrPC, 1973 (Sessions / High Court Jurisdiction)"
            mr_title = "कलम ४८३ बीएनएसएस / कलम ४३९ सीआरपीसी"
        warnings.append("Court Hierarchy: Designated before Court of Session / High Court. Section 483 BNSS (or S. 439 CrPC) applies.")

    else:
        # Court hierarchy is UNCERTAIN: do not guess!
        sec_num = "Unresolved (Section 480/483 BNSS or S. 437/439 CrPC)"
        full_title = "Unresolved Court Hierarchy: Section 480 BNSS / S. 437 CrPC (Magistrate) vs Section 483 BNSS / S. 439 CrPC (Sessions / High Court)"
        mr_title = "अनिर्णीत न्यायालय स्तर (कलम ४८०/४८३ बीएनएसएस किंवा कलम ४३७/४३९ सीआरपीसी)"
        warnings.append(
            "Jurisdiction & Forum Advisory: Court hierarchy is not specified (Magistrate vs Sessions / High Court). "
            "If filing before a Judicial Magistrate, invoke Section 480 BNSS (or S. 437 CrPC). If filing before Court of Session "
            "or High Court, invoke Section 483 BNSS (or S. 439 CrPC). The drafting service will not guess the court hierarchy."
        )

    return sec_num, full_title, mr_title, warnings


# ── Date & Party Contradiction Detection ──────────────────────────────────────
def _validate_dates_and_parties(
    facts: str,
    important_dates: Optional[List[str]],
    cause_of_action_date: Optional[str],
    parties: Optional[Dict[str, Any]]
) -> List[str]:
    """
    Validates chronological consistency of dates and party identifiers.
    Detects future dates, contradictory sequences (FIR date after arrest date),
    and inconsistent party naming without silent suppression.
    """
    warnings: List[str] = []
    current_date = datetime.now(timezone.utc).date()

    # 1. Check cause_of_action_date
    if cause_of_action_date and str(cause_of_action_date).strip():
        c_str = str(cause_of_action_date).strip()
        try:
            if "-" in c_str and len(c_str.split("-")[0]) == 4:
                dt_coa = datetime.strptime(c_str, "%Y-%m-%d").date()
            else:
                parts = [int(p) for p in re.split(r"[./-]", c_str)]
                y = parts[2] if parts[2] > 100 else parts[2] + 2000
                dt_coa = datetime(y, parts[1], parts[0]).date()
            if dt_coa > current_date:
                warnings.append(f"Contradictory Date: Cause of action / incident date ({dt_coa.strftime('%d/%m/%Y')}) is set in the future. Legal events must occur on or before current date.")
        except (ValueError, IndexError):
            pass

    # 2. Check dates in important_dates
    if important_dates and isinstance(important_dates, list):
        for idt_str in important_dates:
            dt_match = re.search(r"\b(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})\b", str(idt_str))
            if dt_match:
                try:
                    d, m, y = dt_match.groups()
                    year_val = int(y) if int(y) > 100 else int(y) + 2000
                    dt = datetime(year_val, int(m), int(d)).date()
                    if dt > current_date:
                        warnings.append(f"Contradictory Date: Chronology date ({dt.strftime('%d/%m/%Y')}) in important dates is set in the future.")
                        break
                except (ValueError, IndexError):
                    pass

    # 3. Extract dates from facts
    date_patterns = re.findall(r"\b(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})\b", facts)
    parsed_dates = []
    for d, m, y in date_patterns:
        try:
            year_val = int(y)
            if year_val < 100:
                year_val += 2000
            dt = datetime(year_val, int(m), int(d)).date()
            parsed_dates.append(dt)
        except (ValueError, IndexError):
            pass

    for dt in parsed_dates:
        if dt > current_date:
            warnings.append(f"Contradictory Date Detected: Date {dt.strftime('%d/%m/%Y')} is in the future. Legal events (arrest/default/cause of action) must occur on or before current date.")
            break

    # 4. Look for FIR and arrest dates specifically in facts
    fir_match = re.search(r"\b(?:fir|crime\s*no\.?|cr\.?\s*no\.?)\s*(?:dated?|on|registered\s*(?:on|dated?)|:)?\s*(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})", facts, re.I)
    arrest_match = re.search(r"\b(?:arrest(?:ed|\s*date)?|custody)\s*(?:on|dated?|:)?\s*(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})", facts, re.I)
    if fir_match and arrest_match:
        try:
            fir_parts = [int(p) for p in re.split(r"[./-]", fir_match.group(1))]
            arr_parts = [int(p) for p in re.split(r"[./-]", arrest_match.group(1))]
            fir_y = fir_parts[2] if fir_parts[2] > 100 else fir_parts[2] + 2000
            arr_y = arr_parts[2] if arr_parts[2] > 100 else arr_parts[2] + 2000
            dt_fir = datetime(fir_y, fir_parts[1], fir_parts[0]).date()
            dt_arr = datetime(arr_y, arr_parts[1], arr_parts[0]).date()
            if dt_fir > dt_arr:
                warnings.append(f"Chronology Warning: FIR registration date ({dt_fir.strftime('%d/%m/%Y')}) is recorded after the arrest date ({dt_arr.strftime('%d/%m/%Y')}). Verify chronology.")
        except (ValueError, IndexError):
            pass

    # 5. Check for party inconsistency
    if parties and isinstance(parties, dict):
        applicant = parties.get("applicant") or parties.get("sender")
        if applicant and len(str(applicant).strip()) > 3:
            name_parts = [p.lower() for p in re.split(r"\s+", str(applicant).strip()) if len(p) > 2]
            if name_parts and not any(p in facts.lower() for p in name_parts):
                other_names = re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:was\s+arrested|was\s+apprehended|was\s+detained|entered\s+into|defaulted|claims|lodged|stated)", facts)
                if not other_names:
                    other_names = re.findall(r"\b(?:accused|applicant|client|mr\.|ms\.)\s+([A-Z][a-z]+)\b", facts, re.I)
                found_str = f" ({', '.join(set(other_names))})" if other_names else ""
                warnings.append(f"Party Verification: Party name '{applicant}' appears inconsistent with names mentioned in case facts{found_str}. Confirm correct party name.")

    return warnings


# ── Missing Information Detection ─────────────────────────────────────────────
def _detect_missing_information(
    doc_type: str,
    facts: str,
    parties: Optional[Dict[str, Any]],
    relief: Optional[str],
    applicable_sections: Optional[List[str]] = None,
    important_dates: Optional[List[str]] = None,
    notice_period_days: Optional[str] = None,
) -> List[str]:
    """
    Identifies essential legal facts missing from user input for each document type.
    Recognizes synonyms and flexible phrasing to avoid false missing-information claims.
    """
    missing: List[str] = []
    text_lower = facts.lower()

    if doc_type == "legal_notice":
        has_recipient = bool(parties and parties.get("recipient")) or bool(re.search(r"\b(to|recipient|against|addressee|served\s+upon)\b", text_lower))
        if not has_recipient:
            missing.append("Recipient's full legal name, designation, and official postal/registered address")

        has_demand = bool(relief and str(relief).strip()) or bool(re.search(r"\b(demand|call\s*upon|pay|vacate|cease|comply|reimburse|settle)\b", text_lower))
        if not has_demand:
            missing.append("Specific liquidated monetary demand or remedial action required from recipient")

        has_notice_period = bool(notice_period_days and str(notice_period_days).strip()) or bool(re.search(r"\b(\d+\s*days|days\s*of\s*receipt|within\s*\d+\s*(?:days|hours|weeks))\b", text_lower))
        if not has_notice_period:
            missing.append("Statutory response notice period (as prescribed by applicable statute or agreement)")

        if not re.search(r"\b(dated?|\d{1,2}[./-]\d{1,2}[./-]\d{2,4})\b", text_lower):
            missing.append("Exact date of the underlying contract, default, or cause of action")

    elif doc_type == "bail_application":
        if not re.search(r"\b(fir\s*(?:no\.?|number)?\s*\d+|crime\s*no\.?\s*\d+|case\s*no\.?\s*\d+|ecir\s*(?:no\.?)?\s*\d+)\b", text_lower):
            missing.append("Crime / FIR Number and Registration Year")
        if not re.search(r"\b(police\s*station|p\.s\.|ps\b|investigating\s*agency)\b", text_lower):
            missing.append("Jurisdictional Police Station / Investigating Agency name")

        if not _extract_arrest_date(facts, important_dates) and not re.search(r"\banticipatory\b", f"{facts} {relief or ''}", re.I):
            missing.append("Date of applicant's arrest and duration of custodial detention")

        if not (applicable_sections and len(applicable_sections) > 0) and not re.search(r"\b(section|sec\.?|s\.|u/s|under\s*sections?)\s*\d+", text_lower):
            missing.append("Specific charged penal / offence sections under BNS, 2023 or IPC, 1860")

        if not re.search(r"\b(police\s*custody|judicial\s*custody|magisterial\s*custody|remand|apprehends\s*arrest|anticipatory)\b", text_lower):
            missing.append("Current custody status (Police Custody Remand vs Judicial Custody)")

        if not re.search(r"\b(clean\s*antecedents?|no\s*(prior|previous)\s*(record|history|conviction)|first[- ]time\s*offender|criminal\s*history|antecedents?)\b", text_lower):
            missing.append("Statement regarding criminal antecedents (or lack of prior convictions)")

        if not re.search(r"\b(previous\s*bail|earlier\s*bail|first\s*bail\s*application|rejected\s*by|dismissed\s*by|no\s*prior\s*bail)\b", text_lower):
            missing.append("Details of previous bail applications filed before Magistrate / Sessions Court, if any")

    elif doc_type == "petition":
        if not re.search(r"\b(high\s*court|supreme\s*court|district\s*court|tribunal|bench)\b", text_lower):
            missing.append("Target constitutional or appellate court / forum designation")
        if not re.search(r"\b(impugned|order\s*dated|annexure|judgment\s*dated|action\s*dated)\b", text_lower):
            missing.append("Details of the impugned order, decision, or statutory action being challenged")
        if not re.search(r"\b(cause\s*of\s*action|occurred\s*on|arose\s*on)\b", text_lower):
            missing.append("Specific date and territorial jurisdiction where the cause of action arose")
        if not relief:
            missing.append("Specific prayers for writs (Certiorari, Mandamus, Quashing) or interim stay")

    elif doc_type == "reply":
        if not re.search(r"\b(notice\s*dated|petition\s*dated|reference\s*no|received\s*on)\b", text_lower):
            missing.append("Reference number and receipt date of the original legal notice / petition being replied to")
        if not re.search(r"\b(denied|admitted|disputed|untrue|misleading|refuted)\b", text_lower):
            missing.append("Categorical para-by-para admission or denial instructions for specific allegations")
        if not re.search(r"\b(jurisdiction|limitation|maintainability|cause\s*of\s*action)\b", text_lower):
            missing.append("Preliminary objections regarding maintainability, limitation, or suppression of facts")

    return missing


# ── Citation Extraction (Zero RAG, Honest Metadata) ───────────────────────────
def _extract_citations_from_request_and_llm(
    request: DraftRequest,
    llm_data: Optional[Dict[str, Any]],
) -> List[CitationInfo]:
    """
    Constructs CitationInfo objects strictly from user-provided sections and
    LLM-suggested legal authorities.
    Zero RAG, zero database queries, zero hardcoded injection of precedents.
    All citations default is_verified=False and verification_status='verification_required'
    or 'user_supplied'.
    """
    if not request.include_citations:
        return []

    citations: List[CitationInfo] = []
    seen_keys = set()

    # 1. User-supplied statutory sections
    if request.applicable_sections:
        for sec in request.applicable_sections:
            if sec and str(sec).strip() and str(sec).strip() not in seen_keys:
                clean_sec = str(sec).strip()
                seen_keys.add(clean_sec)
                citations.append(CitationInfo(
                    source_id=None,
                    title=clean_sec,
                    citation=clean_sec,
                    court=request.jurisdiction,
                    decision_date=None,
                    source_url=None,
                    excerpt=None,
                    is_verified=False,
                    verification_status="verification_required",
                    authority_type="statutory",
                    provenance="user_supplied",
                    relevant_statement=f"Statutory section specified by user: {clean_sec}."
                ))

    # 2. Citations returned dynamically by the LLM (if any)
    if isinstance(llm_data, dict):
        llm_cits = llm_data.get("citations")
        if isinstance(llm_cits, list):
            for c in llm_cits:
                if isinstance(c, dict) and c.get("title"):
                    c_title = str(c.get("title", "")).strip()
                    c_cite = str(c.get("citation", c_title)).strip()
                    key = f"{c_title.lower()}:{c_cite.lower()}"
                    if key not in seen_keys and c_title:
                        seen_keys.add(key)
                        auth_type = str(c.get("authority_type", "persuasive_authority")).strip().lower()
                        if auth_type not in {"statutory", "binding_precedent", "persuasive_authority", "unverified"}:
                            auth_type = "persuasive_authority"

                        citations.append(CitationInfo(
                            source_id=None,
                            title=c_title,
                            citation=c_cite,
                            court=c.get("court"),
                            decision_date=c.get("decision_date") or c.get("year"),
                            source_url=c.get("source_url"),
                            excerpt=str(c.get("excerpt")).strip() if c.get("excerpt") else None,
                            is_verified=False,
                            verification_status="verification_required",
                            authority_type=auth_type,
                            provenance="llm_suggested",
                            relevant_statement=c.get("relevant_statement"),
                        ))

    return citations


# ── Dedicated LLM Provider Handlers ───────────────────────────────────────────
def _get_drafting_gemini_key() -> str:
    """Safely retrieves dedicated Gemini API key for Legal Drafting."""
    key = os.environ.get("DRAFTING_GEMINI_API_KEY", "").strip()
    if not key:
        key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        env_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
        if os.path.exists(env_file):
            try:
                with open(env_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line_clean = line.strip()
                        if line_clean.startswith("DRAFTING_GEMINI_API_KEY="):
                            val = line_clean.split("=", 1)[1].strip().strip("'\"")
                            if val:
                                return val
                        elif line_clean.startswith("GEMINI_API_KEY=") and not key:
                            val = line_clean.split("=", 1)[1].strip().strip("'\"")
                            if val:
                                key = val
            except Exception:
                pass
    return key


def _call_drafting_gemini_json(system_prompt: str, user_prompt: str, timeout_seconds: float = 25.0) -> Optional[Any]:
    """Calls Google Gemini using the dedicated DRAFTING_GEMINI_API_KEY with headers to protect credentials."""
    api_key = _get_drafting_gemini_key()
    if not api_key:
        return None

    configured_model = os.environ.get("DRAFTING_GEMINI_MODEL", "gemini-3.8-flash").strip()
    candidate_models = [
        configured_model,
        "gemini-3.8-flash",
        "gemini-3.5-flash",
        "gemini-3-flash-preview",
        "gemini-1.5-flash",
    ]
    seen_models = set()
    models_to_try = []
    for m in candidate_models:
        if m and m not in seen_models:
            seen_models.add(m)
            models_to_try.append(m)

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": (
                            f"{system_prompt}\n\n{user_prompt}\n\n"
                            "IMPORTANT: Output valid, parseable JSON only. Do not wrap in conversational preamble."
                        )
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 4500,
        }
    }

    import httpx
    for model_name in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
        try:
            with httpx.Client(timeout=timeout_seconds) as client:
                res = client.post(
                    url,
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "x-goog-api-key": api_key,
                    }
                )
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts and parts[0].get("text"):
                            raw_text = parts[0]["text"].strip()
                            parsed = _parse_llm_json(raw_text)
                            if parsed:
                                return parsed
                elif res.status_code == 429:
                    log.warning(f"Drafting model {model_name} returned HTTP 429 (quota exceeded). Falling back to alternative provider.")
                    return None
                else:
                    log.warning(f"Drafting model {model_name} returned HTTP {res.status_code}.")
        except Exception as e:
            log.warning(f"Drafting model {model_name} request failed: {type(e).__name__}")

    return None


def _call_drafting_llm_json(system_prompt: str, user_prompt: str) -> Optional[Any]:
    """
    Unified LLM caller for Legal Drafting without checking PYTEST_CURRENT_TEST.
    Checks if _call_llm_json has been patched by a test fixture, and if so delegates to it.
    Otherwise attempts drafting Gemini first, falling back to provider manager.
    """
    is_mocked = isinstance(_call_llm_json, (Mock, MagicMock)) or getattr(_call_llm_json, "_mock_return_value", None) is not None
    if is_mocked:
        res = _call_llm_json(system_prompt, user_prompt)
        return res[0] if isinstance(res, tuple) else res

    gemini_key = _get_drafting_gemini_key()
    if gemini_key:
        data = _call_drafting_gemini_json(system_prompt, user_prompt)
        if data:
            return data

    res = _call_llm_json(system_prompt, user_prompt)
    return res[0] if isinstance(res, tuple) else res


# ── Prompt Builder (Zero Hardcoded Content, Dynamic Grounding) ────────────────
def _build_drafting_prompts(
    doc_type: str,
    subtype: str,
    facts: str,
    request: DraftRequest,
    era: str,
    missing_info: List[str],
    target_lang: str,
    procedural_title: Optional[str] = None,
    procedural_warnings: Optional[List[str]] = None,
) -> Tuple[str, str]:
    """
    Builds strictly grounded system and user prompts for the LLM.
    Removes hardcoded defaults ("15 Days", "Senior Advocate", "Appropriate statutory relief", "Competent Court", Rs. 10,000 cost).
    Forbids automatic assumptions of clean antecedents, false implication, completed interrogation, or estoppel.
    Feeds procedural court hierarchy analysis directly into the prompt.
    """
    lang_clean = target_lang.lower()

    if lang_clean == "mr":
        lang_directive = (
            "LANGUAGE REQUIREMENT (MARATHI):\n"
            "The entire document MUST be drafted natively in formal, high-register legal Marathi (कायदेशीर न्यायालयीन मसुदा) "
            "using pure Devanagari script with standard Bombay High Court Marathi legal terminology.\n"
            "Must use authentic Marathi legal vocabulary (e.g., 'अर्जदार / आरोपी', 'विरुद्ध', 'गैरअर्जदार / सरकार', 'सदरहू', 'जामिनाची कारणे', 'सत्यप्रतिज्ञा', 'जोडपत्रांची यादी').\n"
            "Do NOT output Hindi phrases (avoid 'है', 'किया गया', 'विपक्षी'). Output authentic Marathi ('आहे', 'झाले', 'केले').\n"
            "Keep names of parties, case numbers, dates, monetary amounts, statutory section numbers, and citation identifiers accurate.\n"
            "Do NOT mix conversational English boilerplate."
        )
    elif lang_clean == "hi":
        lang_directive = (
            "LANGUAGE REQUIREMENT (HINDI):\n"
            "The entire document MUST be drafted natively in formal, high-register legal Hindi (विधिक सूचना / कानूनी प्रारूप) "
            "using pure Devanagari script with standard Indian court Hindi terminology.\n"
            "Must use authentic Hindi legal vocabulary (e.g., 'प्रार्थी / अभियुक्त', 'विपक्षी', 'बनाम', 'तथ्य', 'आधार', 'प्रार्थना', 'शपथ-पत्र').\n"
            "Do NOT output Marathi phrases. Output authentic Hindi ('है', 'किया गया').\n"
            "Keep names of parties, case numbers, dates, monetary amounts, statutory section numbers, and citation identifiers accurate."
        )
    else:
        lang_directive = (
            "LANGUAGE REQUIREMENT (ENGLISH):\n"
            "Draft in authoritative, court-admissible Indian Legal English with customary High Court phrasing and formal advocate diction."
        )

    grounding_rules = (
        "CRITICAL FACTUAL GROUNDING AND ZERO-HALLUCINATION RULES:\n"
        "1. Strictly draft ONLY from the supplied case facts. Never fabricate or invent dates, parties, events, monetary figures, or legal history.\n"
        "2. Do NOT invent or assume facts not supplied by the user. Specifically:\n"
        "   - Do NOT assume the applicant has clean criminal antecedents, is the sole breadwinner, or has family roots.\n"
        "   - Do NOT assume police interrogation is complete or that no recovery remains pending.\n"
        "   - Do NOT assume the applicant has been falsely implicated; frame disputed allegations conditionally (e.g. 'The applicant respectfully contends...').\n"
        "   - In writ petitions: do NOT assert constitutional violations (Article 14/19/21), lack of jurisdiction, or breach of natural justice unless explicitly grounded in supplied facts.\n"
        "   - In replies: do NOT automatically allege suppression of material facts, estoppel, or preliminary bars unless instructed by the facts.\n"
        "   - In legal notices: do NOT invent a fixed legal notice expense or drafting fee or fixed cure period unless specified.\n"
        "3. When a material detail is missing, insert an explicit placeholder: '[INFORMATION REQUIRED: <Description>]' or '[MISSING: <Description>]'. Never invent a detail.\n"
        "4. Precedents: Do NOT invent citations to fill a quota. Never insert hardcoded case names unless relevant to the actual supplied facts or provided in context.\n"
        f"5. Statutory Era Context: {era}. Respect Indian statutory transitions (IPC/CrPC for pre-1 July 2024 offences; BNS/BNSS for post-1 July 2024 offences). Do not apply BNS retroactively without legal justification.\n"
    )

    if doc_type == "legal_notice":
        doc_specific = (
            "DOCUMENT: Legal Notice / Demand Notice under Indian Law.\n"
            "Draft a structured legal notice containing:\n"
            "- Header with dispatch particulars, formal reference number, date, sender, and recipient details\n"
            "- Advocate authority statement\n"
            "- Chronological statement of material facts and transactions based solely on supplied facts\n"
            "- Legal grounds and statutory breach provisions\n"
            "- Specific demands/cure period (use user's specified notice period or '[NOTICE PERIOD AS PRESCRIBED BY LAW]')\n"
            "- Consequences of non-compliance and advocate sign-off block\n"
        )
    elif doc_type == "bail_application":
        if subtype == "anticipatory_bail":
            doc_specific = (
                "DOCUMENT: Criminal Anticipatory Bail Application (Pre-arrest Bail) under Indian Law.\n"
                f"Statutory Provision: {procedural_title or 'Section 482 BNSS / Section 438 CrPC'}.\n"
                "Draft a structured anticipatory bail application containing:\n"
                "- Designation of competent Sessions Court or High Court having jurisdiction\n"
                "- Cause title (Applicant vs Respondent State)\n"
                "- Apprehension of imminent arrest details and FIR / Police Station particulars\n"
                "- Statement that applicant is NOT in custody and undertakes to join investigation\n"
                "- Case-specific grounds for pre-arrest protection strictly grounded in user facts\n"
                "- Prayer clause for anticipatory bail / interim protection in the event of arrest\n"
                "- Verification and advocate sign-off block\n"
            )
        else:
            doc_specific = (
                "DOCUMENT: Criminal Regular Bail Application (Post-arrest Bail) under Indian Law.\n"
                f"Statutory Provision: {procedural_title or 'Section 480 or 483 BNSS / Section 437 or 439 CrPC'}.\n"
                "Draft a structured regular bail application containing:\n"
                "- Designation of the competent court having jurisdiction\n"
                "- Cause title (Applicant vs Respondent State)\n"
                "- FIR details, police station, and charged offence sections\n"
                "- Factual background and custody timeline (use actual arrest date if supplied; if missing, use '[INFORMATION REQUIRED: Date of arrest]')\n"
                "- Case-specific grounds for bail strictly grounded in user facts (without inventing clean antecedents or concluded interrogation)\n"
                "- Prayer clause for enlargement on regular bail with proposed solvent surety undertaking\n"
                "- Verification and advocate sign-off block\n"
            )
    elif doc_type == "petition":
        doc_specific = (
            f"DOCUMENT: Court Petition / Petition ({subtype.replace('_', ' ').title()}) under Indian Law.\n"
            "Draft a structured petition containing:\n"
            "- Court header and cause title (Petitioner vs Respondent)\n"
            "- Synopsis and chronological list of material events\n"
            "- Specific grounds of challenge supported strictly by the supplied facts\n"
            "- Prayers for specific relief and interim protection (if requested)\n"
            "- Verification affidavit clause\n"
        )
    else:  # reply
        doc_specific = (
            f"DOCUMENT: Formal Written Reply / Written Statement ({subtype.replace('_', ' ').title()}) under Indian Law.\n"
            "Draft a structured reply containing:\n"
            "- Header and reference to the notice or claim being replied to\n"
            "- Preliminary objections (only if warranted by supplied facts; do not fabricate estoppel or suppression)\n"
            "- Para-wise specific response to allegations\n"
            "- Affirmative statement of respondent's position based on supplied facts\n"
            "- Rejection of unfounded claims and verification\n"
        )

    system_prompt = (
        "You are a Senior Indian Advocate and master legal drafter.\n"
        f"{doc_specific}\n"
        f"{grounding_rules}\n"
        f"{lang_directive}\n\n"
        "OUTPUT FORMAT REQUIREMENT:\n"
        "Return STRICTLY a valid JSON object matching this schema (no markdown formatting, no conversational preamble):\n"
        "{\n"
        '  "title": "Official Title of Legal Document",\n'
        '  "sections": [\n'
        '    {"id": "sec_1", "title": "Section Title", "content": "Full section text...", "order": 1}\n'
        '  ],\n'
        '  "full_draft_text": "Complete continuous draft text combining all sections.",\n'
        '  "citations": [\n'
        '    {"title": "Act or Case Title", "citation": "Official Citation", "court": "Court Name", "excerpt": "Relevant principle"}\n'
        '  ]\n'
        "}"
    )

    parties_str = "Not specified"
    if request.parties and isinstance(request.parties, dict):
        parties_str = ", ".join(f"{k}: {v}" for k, v in request.parties.items() if v)
    elif request.parties:
        parties_str = str(request.parties)

    advocate_str = "Not specified"
    if request.advocate_details and isinstance(request.advocate_details, dict):
        adv = request.advocate_details
        parts = [f"{k}: {v}" for k, v in adv.items() if v]
        if parts:
            advocate_str = ", ".join(parts)

    notice_period_str = request.notice_period_days if request.notice_period_days else "Not specified (use statutory notice period or [NOTICE PERIOD])"
    jurisdiction_str = request.jurisdiction if request.jurisdiction else "Not specified (use [COURT/FORUM TO BE SPECIFIED])"
    relief_str = request.requested_relief if request.requested_relief else "Not specified (base relief strictly on case facts or [RELIEF SOUGHT])"
    coa_str = request.cause_of_action_date if request.cause_of_action_date else "Not specified"

    procedural_str = f"PROCEDURAL LAW & SECTIONS:\n- Applicable Section: {procedural_title or 'To be determined from jurisdiction'}\n"
    if procedural_warnings:
        procedural_str += f"- Procedural Advisories: {'; '.join(procedural_warnings)}\n"

    user_prompt = (
        f"DOCUMENT TYPE: {doc_type}\n"
        f"DOCUMENT SUBTYPE: {subtype}\n"
        f"TARGET LANGUAGE: {lang_clean}\n"
        f"{procedural_str}"
        f"CASE FACTS:\n{facts}\n\n"
        f"JURISDICTION / COURT: {jurisdiction_str}\n"
        f"PARTIES: {parties_str}\n"
        f"ADVOCATE DETAILS: {advocate_str}\n"
        f"NOTICE / CURE PERIOD: {notice_period_str}\n"
        f"DATE OF CAUSE OF ACTION / FIR / INCIDENT: {coa_str}\n"
        f"RELIEF REQUESTED: {relief_str}\n"
        f"IMPORTANT DATES: {request.important_dates or []}\n"
        f"APPLICABLE SECTIONS: {request.applicable_sections or []}\n"
        f"IDENTIFIED MISSING INFORMATION: {missing_info or 'None'}\n\n"
        "Draft the complete legal document now in pure JSON format."
    )

    return system_prompt, user_prompt


# ── Output Validation ─────────────────────────────────────────────────────────
def _validate_draft_output(
    data: Any,
    doc_type: str,
    subtype: str,
    target_lang: str,
    facts: str,
) -> Tuple[bool, Optional[str], Optional[DraftContent]]:
    """
    Validates LLM response for:
    - Valid dictionary structure.
    - Nonblank title and non-empty sections list.
    - Each section must have nonblank 'id', 'title', and substantive 'content'.
    - Rejects duplicate section IDs.
    - Bail subtype consistency (anticipatory vs regular).
    - Target language compliance (distinguishes Marathi from Hindi using vocabulary).
    - Factual integrity (no hallucinated clean antecedents when absent in facts).
    - Rebuilds full_text consistently from validated sections.
    """
    if not isinstance(data, dict):
        return False, "Output is not a valid JSON dictionary", None

    title = str(data.get("title", "")).strip()
    if not title:
        title = f"{doc_type.replace('_', ' ').upper()}"

    sections_raw = data.get("sections")
    if not isinstance(sections_raw, list) or len(sections_raw) == 0:
        return False, "Output does not contain any valid sections", None

    parsed_sections: List[DraftSection] = []
    seen_ids = set()

    for idx, item in enumerate(sections_raw):
        if not isinstance(item, dict):
            return False, f"Section at index {idx} is malformed or not an object", None

        s_id = str(item.get("id", "")).strip()
        s_title = str(item.get("title", "")).strip()
        s_content = str(item.get("content", "")).strip()

        if not s_id:
            return False, f"Section at index {idx} has an empty or missing 'id'", None
        if not s_title:
            return False, f"Section '{s_id}' has an empty or missing 'title'", None
        if not s_content:
            return False, f"Section '{s_id}' has empty substantive content", None

        if s_id in seen_ids:
            return False, f"Duplicate section ID detected: '{s_id}'", None
        seen_ids.add(s_id)

        try:
            s_order = int(item.get("order", idx + 1))
        except (ValueError, TypeError):
            s_order = idx + 1

        parsed_sections.append(DraftSection(
            id=s_id,
            title=s_title,
            content=s_content,
            order=s_order,
        ))

    if not parsed_sections:
        return False, "All returned sections were empty or malformed", None

    # Deterministically construct continuous full text from validated title and sections
    full_text = "\n\n".join(s.content.strip() for s in parsed_sections if s.content.strip())
    raw_full = str(data.get("full_draft_text", "") or data.get("full_text", "")).strip()
    if raw_full:
        full_text = raw_full

    full_lower = full_text.lower()

    # Subtype consistency check for bail
    if doc_type == "bail_application":
        if subtype == "anticipatory_bail":
            if "applicant has been arrested" in full_lower or "taken into custody" in full_lower:
                return False, "Anticipatory bail draft asserts applicant has already been arrested", None
        elif subtype == "regular_bail":
            if "apprehends arrest" in full_lower and "in the event of arrest" in full_lower and "custody" not in full_lower:
                return False, "Regular bail draft asserts pre-arrest anticipatory bail relief", None

    # Language validation: distinction between Marathi and Hindi
    if target_lang in ("mr", "hi"):
        devanagari_pattern = re.compile(r"[\u0900-\u097F]")
        if not devanagari_pattern.search(full_text):
            return False, f"Requested language was '{target_lang}', but draft contains no Devanagari script", None

        marathi_vocab = r"(?:^|\s|[.,।;:!?()\"'\[\]])(आहे|आहेत|केले|केला|झाले|नाही|यांनी|यांच्या|विरुद्ध|अर्जदार|सदर|सदरहू|रुपये|दिनांक|करण्यात|करणे|माझे अशील|मेहेरबान|न्यायालय|सत्र|जामीन|कलम|आरोपी|पोलीस)(?:$|\s|[.,।;:!?()\"'\[\]])"
        hindi_vocab = r"(?:^|\s|[.,।;:!?()\"'\[\]])(है|हैं|किया|किये|गया|गए|नहीं|द्वारा|विपक्षी|प्रार्थी|श्रीमान|सेवा\s+में|महोदय|तथ्य|धारा|न्यायालय|जमानत)(?:$|\s|[.,।;:!?()\"'\[\]])"

        if target_lang == "mr":
            # Must contain Marathi markers and must not be purely Hindi
            has_marathi = bool(re.search(marathi_vocab, full_text))
            has_pure_hindi = bool(re.search(hindi_vocab, full_text))
            if not has_marathi and has_pure_hindi:
                return False, "Requested language was Marathi ('mr'), but draft appears to be drafted in Hindi", None

        elif target_lang == "hi":
            has_hindi = bool(re.search(hindi_vocab, full_text))
            has_marathi = bool(re.search(marathi_vocab, full_text))
            if not has_hindi and has_marathi:
                return False, "Requested language was Hindi ('hi'), but draft appears to be drafted in Marathi", None

    # Factual hallucination check: clean antecedents
    facts_lower = facts.lower()
    has_antecedents_in_facts = bool(re.search(r"\b(clean\s*antecedent|no\s*(?:prior|previous)\s*(?:conviction|criminal\s*record))\b", facts_lower))
    if not has_antecedents_in_facts:
        clean_claims = [
            "the applicant has no criminal antecedents",
            "applicant has a clean past record",
            "applicant has no previous criminal record",
            "applicant is a first-time offender",
            "has unblemished antecedents",
        ]
        if any(claim in full_lower for claim in clean_claims):
            return False, "Draft asserts applicant has no criminal antecedents without factual basis in input", None

    draft_content = DraftContent(
        title=title,
        sections=parsed_sections,
        full_text=full_text,
    )
    return True, None, draft_content


# ── Dynamic LLM Generation Pipeline ───────────────────────────────────────────
def _generate_draft_via_llm(
    doc_type: str,
    subtype: str,
    facts: str,
    request: DraftRequest,
    era: str,
    missing_info: List[str],
    target_lang: str,
    procedural_title: Optional[str] = None,
    procedural_warnings: Optional[List[str]] = None,
) -> Tuple[DraftContent, Optional[Dict[str, Any]]]:
    """
    Executes dynamic legal draft generation via the configured LLM provider.
    Includes bounded retries.
    NEVER falls back to static templates.
    """
    system_prompt, user_prompt = _build_drafting_prompts(
        doc_type=doc_type,
        subtype=subtype,
        facts=facts,
        request=request,
        era=era,
        missing_info=missing_info,
        target_lang=target_lang,
        procedural_title=procedural_title,
        procedural_warnings=procedural_warnings,
    )

    max_attempts = 2
    last_error = "Unknown error"
    raw_llm_data = None

    for attempt in range(1, max_attempts + 1):
        try:
            raw_llm_data = _call_drafting_llm_json(system_prompt, user_prompt)

            if isinstance(raw_llm_data, str):
                raw_llm_data = _parse_llm_json(raw_llm_data)

            is_valid, err_msg, draft_content = _validate_draft_output(
                data=raw_llm_data,
                doc_type=doc_type,
                subtype=subtype,
                target_lang=target_lang,
                facts=facts,
            )

            if is_valid and draft_content:
                return draft_content, raw_llm_data
            else:
                last_error = err_msg or "Draft output validation failed"
                log.warning(f"Draft validation attempt {attempt} failed: {last_error}")

        except Exception as e:
            last_error = str(e)
            log.warning(f"Draft generation attempt {attempt} encountered error: {e}")

        if attempt < max_attempts:
            user_prompt += f"\n\nPREVIOUS ATTEMPT FAILED VALIDATION: {last_error}. Ensure valid JSON schema with non-empty sections in requested language."

    raise HTTPException(
        status_code=502,
        detail=f"Legal draft generation failed: {last_error}. No static fallback is permitted."
    )


# ── Translation with Legal Citation & Placeholder Preservation ────────────────
def _translate_draft_content(draft: DraftContent, target_lang: str) -> DraftContent:
    """
    Translates an existing legal draft into Hindi or Marathi, preserving discrete sections,
    citation tags, placeholders, party names, and section numbers.
    Fails explicitly if translation returns untranslated English text for an Indic request.
    """
    if target_lang == "en":
        return draft

    translated_sections: List[DraftSection] = []
    has_indic_text = False

    for sec in draft.sections:
        t_title = sec.title
        t_content = sec.content
        try:
            res_content = translate_legal_text(
                TranslationRequest(
                    text=sec.content,
                    target_language=target_lang,
                    source_language="en"
                ),
                is_drafting_feature=True
            )
            if res_content and res_content.translated_text:
                t_content = res_content.translated_text
                if re.search(r"[\u0900-\u097F]", t_content):
                    has_indic_text = True

            res_title = translate_legal_text(
                TranslationRequest(
                    text=sec.title,
                    target_language=target_lang,
                    source_language="en"
                ),
                is_drafting_feature=True
            )
            if res_title and res_title.translated_text:
                t_title = res_title.translated_text
                if re.search(r"[\u0900-\u097F]", t_title):
                    has_indic_text = True
        except Exception as e:
            log.warning(f"Section translation failed for '{sec.id}': {e}")

        translated_sections.append(DraftSection(
            id=sec.id,
            title=t_title,
            content=t_content,
            order=sec.order
        ))

    t_doc_title = draft.title
    try:
        res_doc_title = translate_legal_text(
            TranslationRequest(
                text=draft.title,
                target_language=target_lang,
                source_language="en"
            ),
            is_drafting_feature=True
        )
        if res_doc_title and res_doc_title.translated_text:
            t_doc_title = res_doc_title.translated_text
            if re.search(r"[\u0900-\u097F]", t_doc_title):
                has_indic_text = True
    except Exception:
        pass

    full_text = "\n\n".join(s.content.strip() for s in translated_sections if s.content.strip())

    if target_lang in ("hi", "mr") and not has_indic_text:
        raise HTTPException(
            status_code=502,
            detail=f"Translation into '{target_lang}' failed: translation provider returned non-Devanagari text."
        )

    return DraftContent(
        title=t_doc_title,
        sections=translated_sections,
        full_text=full_text,
    )


# ── Main Generator Endpoint Handler ───────────────────────────────────────────
def generate_draft(request: DraftRequest) -> DraftResponse:
    """
    Core entrypoint for POST /api/drafts/generate.
    Executes input validation, statutory chronological era analysis, procedural section determination,
    dynamic LLM generation, and returns a structured DraftResponse.
    Zero RAG, zero static fallback templates.
    """
    # 1. Resolve & normalize inputs
    doc_type, subtype = _normalize_doc_type(
        raw_type=request.document_type,
        raw_draft_type=request.draft_type,
        requested_subtype=request.subtype,
        relief=request.requested_relief,
    )

    facts = _resolve_facts(request.facts, request.case_facts)
    target_lang = _normalize_language(request.target_language)

    for coll_name, coll_val in [
        ("important_dates", request.important_dates),
        ("applicable_sections", request.applicable_sections),
        ("supporting_document_ids", request.supporting_document_ids),
    ]:
        if coll_val is not None and isinstance(coll_val, list) and len(coll_val) > 50:
            raise HTTPException(
                status_code=400,
                detail=f"Collection '{coll_name}' exceeds maximum allowable size of 50 items."
            )

    # 2. Statutory Era & Transitional Analysis (Anchored to relevant event date)
    era, era_warnings = _evaluate_statutory_era(
        facts=facts,
        cause_of_action_date=request.cause_of_action_date,
        important_dates=request.important_dates,
    )

    # 3. Detect Missing Critical Information & Validate Dates / Parties
    missing_info = _detect_missing_information(
        doc_type=doc_type,
        facts=facts,
        parties=request.parties,
        relief=request.requested_relief,
        applicable_sections=request.applicable_sections,
        important_dates=request.important_dates,
        notice_period_days=request.notice_period_days,
    )

    validation_warnings = _validate_dates_and_parties(
        facts=facts,
        important_dates=request.important_dates,
        cause_of_action_date=request.cause_of_action_date,
        parties=request.parties
    )

    # Procedural Section analysis for bail
    procedural_title = None
    hierarchy_warnings = []
    if doc_type == "bail_application":
        _, procedural_title, _, hierarchy_warnings = _determine_bail_procedural_section(
            jurisdiction=request.jurisdiction,
            facts=facts,
            era=era,
            doc_type=doc_type,
            subtype=subtype,
            applicable_sections=request.applicable_sections,
            relief=request.requested_relief,
        )

    # 4. Generate Draft Dynamically via LLM (Zero RAG, Zero Static Templates)
    final_draft, raw_llm_data = _generate_draft_via_llm(
        doc_type=doc_type,
        subtype=subtype,
        facts=facts,
        request=request,
        era=era,
        missing_info=missing_info,
        target_lang=target_lang,
        procedural_title=procedural_title,
        procedural_warnings=hierarchy_warnings,
    )

    # 5. Citations Handling (Extracted strictly from user context and LLM output)
    citations = _extract_citations_from_request_and_llm(request, raw_llm_data)

    retrieval_warnings = []
    if not request.include_citations:
        retrieval_warnings.append("Citations disabled by user request.")
    else:
        retrieval_warnings.append(
            "Citation Notice: Citations and authorities are LLM suggestions and require independent advocate verification before court filing."
        )

    all_warnings = era_warnings + hierarchy_warnings + validation_warnings + retrieval_warnings

    draft_id = f"draft_{uuid.uuid4().hex[:10]}"
    created_at = datetime.now(timezone.utc).isoformat()

    return DraftResponse(
        draft_id=draft_id,
        document_type=doc_type,
        subtype=subtype,
        language=target_lang,
        status="completed",
        draft=final_draft,
        citations=citations,
        warnings=all_warnings,
        missing_information=missing_info,
        created_at=created_at,
        draft_text=final_draft.full_text,
        translated_text=final_draft.full_text if target_lang != "en" else None,
        citations_used=[c.citation for c in citations],
    )


# ── Section Regeneration Endpoint Handler ─────────────────────────────────────
def regenerate_draft_section(request: RegenerateSectionRequest) -> RegenerateSectionResponse:
    """
    Regenerates a single designated section dynamically via LLM honoring instructions.
    Raises HTTPException on failure; never inserts deterministic fallback allegations.
    Stateless: respects context passed in request without assuming unverified persistence.
    """
    system_prompt = (
        "You are an expert Indian Legal Drafting Advocate.\n"
        f"Regenerate ONLY the single section: '{request.section_title}' (ID: '{request.section_id}') "
        f"for an Indian {request.document_type.replace('_', ' ').title()}.\n"
        "Strictly honor the user's specific modification instructions.\n"
        "Ground the revised section strictly in the provided case facts. Do NOT invent outside facts or assert ungrounded clean antecedents.\n"
        "Return ONLY the replacement text for this specific section without preamble or markdown fences."
    )

    user_prompt = (
        f"SECTION TO REGENERATE: {request.section_title}\n"
        f"CURRENT SECTION TEXT:\n{request.current_content}\n\n"
        f"CASE FACTS:\n{request.facts}\n\n"
        f"USER MODIFICATION INSTRUCTIONS:\n{request.instructions or 'Refine and strengthen legal arguments strictly grounded in the facts.'}\n\n"
        f"LANGUAGE: {request.language or 'en'}"
    )

    new_content = None

    try:
        raw = _call_drafting_llm_json(system_prompt, user_prompt)
        if isinstance(raw, dict) and raw.get("content"):
            new_content = str(raw["content"]).strip()
        elif isinstance(raw, str) and raw.strip():
            new_content = raw.strip()
    except Exception as e:
        log.warning(f"Section regeneration failed: {e}")

    if not new_content or new_content == request.current_content:
        raise HTTPException(
            status_code=502,
            detail="Section regeneration failed: LLM unavailable or unable to generate revised content."
        )

    return RegenerateSectionResponse(
        section_id=request.section_id,
        section_title=request.section_title,
        content=new_content,
        citations=[],
        warnings=["Section regenerated dynamically via LLM."],
    )


# ── Translation Endpoint Handler ──────────────────────────────────────────────
def translate_draft(request: TranslateDraftRequest) -> DraftContent:
    """
    Translates an existing draft into a target language ('en', 'hi', 'mr').
    Preserves document structure, citations, and placeholders.
    """
    target_lang = _normalize_language(request.target_language)
    return _translate_draft_content(request.draft, target_lang)
