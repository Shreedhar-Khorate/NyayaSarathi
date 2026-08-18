"""
Legal Parser for Indian Court Decisions.

Extracts structured metadata from judgment titles and CNR codes:
- Case type (e.g., CR. MISC. → bail)
- Case number and year
- Petitioner and respondent names
- Court name from CNR prefix
"""

import re
from typing import Dict, Optional

# ── Title Parsing ────────────────────────────────────────────────────
# Typical format: "CR. MISC./43068/2023 of PALTU KUMAR Vs The State of Bihar"
#                  CASE_TYPE/NUMBER/YEAR of PETITIONER Vs RESPONDENT

_TITLE_PATTERN = re.compile(
    r"^(?P<case_type_raw>.+?)\s*/\s*(?P<case_number>\d+)\s*/\s*(?P<case_year>\d{4})"
    r"\s+of\s+(?P<petitioner>.+?)\s+[Vv][Ss]\.?\s+(?P<respondent>.+)$",
    re.IGNORECASE
)

# Fallback: just extract case type before first /
_TITLE_FALLBACK = re.compile(
    r"^(?P<case_type_raw>[A-Za-z\.\s\(\)]+)\s*/",
    re.IGNORECASE
)


def parse_title(title: Optional[str]) -> Dict[str, Optional[str]]:
    """
    Parse an Indian court judgment title into structured fields.

    Returns dict with: case_type_raw, case_number, case_year,
                        petitioner, respondent
    """
    result = {
        "case_type_raw": None,
        "case_number": None,
        "case_year": None,
        "petitioner": None,
        "respondent": None,
    }

    if not title or not title.strip():
        return result

    title = title.strip()

    # Try full pattern
    m = _TITLE_PATTERN.match(title)
    if m:
        result["case_type_raw"] = m.group("case_type_raw").strip()
        result["case_number"] = m.group("case_number").strip()
        result["case_year"] = m.group("case_year").strip()
        result["petitioner"] = _clean_name(m.group("petitioner"))
        result["respondent"] = _clean_name(m.group("respondent"))
        return result

    # Fallback: extract case type only
    m = _TITLE_FALLBACK.match(title)
    if m:
        result["case_type_raw"] = m.group("case_type_raw").strip()

    # Try to extract petitioner/respondent from "Vs" split
    vs_match = re.split(r"\s+[Vv][Ss]\.?\s+", title, maxsplit=1)
    if len(vs_match) == 2:
        # Petitioner is after "of " in the first part
        of_split = vs_match[0].rsplit(" of ", 1)
        if len(of_split) == 2:
            result["petitioner"] = _clean_name(of_split[1])
        result["respondent"] = _clean_name(vs_match[1])

    return result


def _clean_name(name: str) -> str:
    """Clean a party name."""
    name = name.strip().rstrip(".")
    # Remove trailing "and ORS", "& ORS", "& ANR"
    name = re.sub(r"\s+and\s+O[Rr][Ss]\.?$", "", name, flags=re.IGNORECASE)
    name = re.sub(r"\s*&\s*O[Rr][Ss]\.?$", "", name, flags=re.IGNORECASE)
    name = re.sub(r"\s*&\s*A[Nn][Rr]\.?$", "", name, flags=re.IGNORECASE)
    return name.strip()


# ── Case Type Normalization ──────────────────────────────────────────
# Maps raw case type codes from titles to broad legal categories.

_CASE_TYPE_MAP = {
    # Bail / Criminal Miscellaneous
    "cr. misc.": "bail",
    "cr.misc.": "bail",
    "crm(m)": "bail",
    "crm": "bail",
    "crlmc": "bail",
    "crl.m.c.": "bail",
    "crl.m.c": "bail",
    "crl. misc.": "bail",
    "bail appln.": "bail",
    "ba": "bail",
    "abp": "bail",
    "anticipatory bail": "bail",

    # Criminal Appeal
    "crl.a": "criminal_appeal",
    "crl.a.": "criminal_appeal",
    "cra": "criminal_appeal",
    "criminal appeal": "criminal_appeal",
    "crl. appeal": "criminal_appeal",

    # Criminal Revision
    "crl.r": "criminal_revision",
    "crl.rev.": "criminal_revision",
    "criminal revision": "criminal_revision",
    "crr": "criminal_revision",

    # Writ Petition (Civil)
    "wp(c)": "writ_civil",
    "w.p.(c)": "writ_civil",
    "wpc": "writ_civil",
    "writ petition (civil)": "writ_civil",
    "wp (c)": "writ_civil",
    "w.p.(c).": "writ_civil",
    "wp(c).": "writ_civil",

    # Writ Petition (Criminal)
    "wp(crl)": "writ_criminal",
    "w.p.(crl)": "writ_criminal",
    "wp(crl.)": "writ_criminal",
    "writ petition (criminal)": "writ_criminal",

    # Civil Suit
    "cs": "civil",
    "os": "civil",
    "civil suit": "civil",
    "s": "civil",

    # Civil Appeal / Second Appeal
    "sa": "civil_appeal",
    "rsa": "civil_appeal",
    "rfa": "civil_appeal",
    "fa": "civil_appeal",
    "first appeal": "civil_appeal",
    "second appeal": "civil_appeal",
    "mat": "civil_appeal",
    "mat.": "civil_appeal",

    # Appeal from Order
    "fao": "appeal",
    "fao(os)": "appeal",
    "co": "appeal",
    "civil revision": "appeal",

    # Motor Accident
    "mac": "motor_accident",
    "mact": "motor_accident",
    "macp": "motor_accident",
    "mac app.": "motor_accident",
    "fao(mac)": "motor_accident",

    # Commercial / Company
    "cp": "commercial",
    "company petition": "commercial",
    "com.a": "commercial",
    "arb.p.": "commercial",
    "arb. p.": "commercial",
    "arb.a.": "commercial",

    # Tax
    "ta": "tax",
    "ita": "tax",
    "tax appeal": "tax",
    "itat": "tax",
    "ita.": "tax",

    # Family / Matrimonial
    "matrimonial": "family",
    "guardian": "family",
    "fc": "family",

    # Consumer
    "consumer": "consumer",
    "cc": "consumer",

    # Property
    "rp": "property",
    "land": "property",
    "la": "property",

    # Contempt
    "cont.cas(c)": "contempt",
    "cont.cas(crl)": "contempt",
    "contempt": "contempt",

    # Criminal Petition / Quashing
    "crl.o.p.": "criminal",
    "crl.p.": "criminal",
    "quashing": "criminal",

    # Execution
    "ep": "execution",
    "ex.p.": "execution",

    # Review
    "rp": "review",
    "review": "review",

    # PIL
    "pil": "pil",
    "w.p.(pil)": "pil",
}


def normalize_case_type(raw_case_type: Optional[str]) -> str:
    """
    Normalize a raw case type code to a broad legal category.
    Returns 'other' if the case type is unknown.
    """
    if not raw_case_type:
        return "other"

    key = raw_case_type.strip().lower()

    # Direct lookup
    if key in _CASE_TYPE_MAP:
        return _CASE_TYPE_MAP[key]

    # Partial match
    for pattern, category in _CASE_TYPE_MAP.items():
        if pattern in key or key in pattern:
            return category

    return "other"


# ── Court Mapping from CNR prefix ────────────────────────────────────
# CNR prefixes indicate the originating court.

_COURT_PREFIX_MAP = {
    "BRHC": "Patna High Court",
    "HCBM": "Bombay High Court",
    "DLHC": "Delhi High Court",
    "MDHC": "Madras High Court",
    "CLHC": "Calcutta High Court",
    "WBCH": "Calcutta High Court",
    "WBHC": "Calcutta High Court",
    "KRHC": "Karnataka High Court",
    "APHC": "Andhra Pradesh High Court",
    "GTHC": "Gauhati High Court",
    "JKHC": "Jharkhand High Court",
    "MPHC": "Madhya Pradesh High Court",
    "RJHC": "Rajasthan High Court",
    "PHHC": "Punjab & Haryana High Court",
    "KLHC": "Kerala High Court",
    "GUHC": "Gujarat High Court",
    "CGHC": "Chhattisgarh High Court",
    "HCHP": "Himachal Pradesh High Court",
    "UPHC": "Uttarakhand High Court",
    "ORHC": "Orissa High Court",
    "TCHC": "Telangana High Court",
    "SKHC": "Sikkim High Court",
    "MGHC": "Meghalaya High Court",
    "MNHC": "Manipur High Court",
    "TRHC": "Tripura High Court",
}

# Also map bench codes
_BENCH_COURT_MAP = {
    "patnahc": "Patna High Court",
    "bombayhc": "Bombay High Court",
    "delhihc": "Delhi High Court",
    "madrashc": "Madras High Court",
    "calcuttahc": "Calcutta High Court",
    "calcutta": "Calcutta High Court",
    "karnatakaHC": "Karnataka High Court",
    "newos": "Bombay High Court",
}


def extract_court_name(
    cnr: Optional[str],
    bench: Optional[str] = None,
    source: Optional[str] = None,
) -> str:
    """
    Extract court name from CNR prefix and/or bench code.
    """
    if source == "sc":
        return "Supreme Court of India"

    # Try bench code first if provided
    if bench:
        bench_lower = bench.lower()
        for key, court in _BENCH_COURT_MAP.items():
            if key.lower() in bench_lower:
                return court

    # Try CNR prefix (first 4 chars)
    if cnr:
        prefix = cnr[:4].upper()
        if prefix in _COURT_PREFIX_MAP:
            return _COURT_PREFIX_MAP[prefix]

        # Try prefix patterns
        for key, court in _COURT_PREFIX_MAP.items():
            if cnr.upper().startswith(key):
                return court

        if cnr.upper().startswith("WB"):
            return "Calcutta High Court"
        if cnr.upper().startswith("BR"):
            return "Patna High Court"
        if cnr.upper().startswith("MH") or cnr.upper().startswith("HCBM"):
            return "Bombay High Court"
        if cnr.upper().startswith("DL"):
            return "Delhi High Court"

    return "High Court"
