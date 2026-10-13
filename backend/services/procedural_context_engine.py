"""
NyayaSarathi Legal War Room — Procedural Context Engine
Dynamically determines:
1. Exact judicial forum (Supreme Court, High Court, Sessions/Trial Court, Magistrate).
2. Procedural posture (concluded/decided appeal vs pending appeal vs trial vs bail vs contempt).
3. Consistent party roles (Appellant/Petitioner vs Respondent/State).
4. Statutory era & transition rules (IPC/CrPC vs BNS/BNSS/BSA based on 1 July 2024 cutoff and Section 531 BNSS).
5. Stage-appropriate procedural next steps (prohibiting invalid High Court rejoinders or bail applications for concluded appeals).
Zero hardcoded case names. Completely dynamic and rule-grounded.
"""

import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from logger import get_logger

log = get_logger("nyayasarathi.procedural_context_engine")

# 1 July 2024: Date of enforcement of Bharatiya Nyaya Sanhita & Bharatiya Nagarik Suraksha Sanhita
NEW_CRIMINAL_LAWS_CUTOFF = datetime(2024, 7, 1)

PROVISION_CROSS_WALK = {
    "ipc_302": {"old": "Section 302 IPC", "new": "Section 103(1) BNS, 2023", "subject": "Punishment for Murder"},
    "ipc_300_exc_4": {"old": "Exception 4 to Section 300 IPC", "new": "Exception 4 to Section 101 BNS, 2023", "subject": "Sudden Fight in Heat of Passion"},
    "ipc_304_part_2": {"old": "Section 304 Part II IPC", "new": "Section 105 BNS, 2023", "subject": "Culpable Homicide Not Amounting to Murder (Knowledge without Intention)"},
    "ipc_307": {"old": "Section 307 IPC", "new": "Section 109 BNS, 2023", "subject": "Attempt to Murder"},
    "ipc_498a": {"old": "Section 498A IPC", "new": "Section 85 & 86 BNS, 2023", "subject": "Cruelty by Husband or Relatives"},
    "crpc_41": {"old": "Section 41 CrPC", "new": "Section 35(1) BNSS, 2023", "subject": "Police Power of Arrest Without Warrant"},
    "crpc_41a": {"old": "Section 41A CrPC", "new": "Section 35(3) BNSS, 2023", "subject": "Mandatory Notice of Appearance Before Police"},
    "crpc_313": {"old": "Section 313(5) CrPC", "new": "Section 351(5) BNSS, 2023", "subject": "Written Statement of Accused"},
    "crpc_428": {"old": "Section 428 CrPC", "new": "Section 468 BNSS, 2023", "subject": "Set-off of Pre-trial Detention Against Sentence"},
    "crpc_438": {"old": "Section 438 CrPC", "new": "Section 482 BNSS, 2023", "subject": "Anticipatory Bail"},
    "crpc_439": {"old": "Section 439 CrPC", "new": "Section 483 BNSS, 2023", "subject": "Special Powers of High Court/Sessions on Bail"},
}


def evaluate_statutory_era(session: Dict[str, Any], text: str) -> Dict[str, Any]:
    """
    Determines whether IPC/CrPC or BNS/BNSS applies under Section 531 BNSS and Article 20(1) Constitution of India.
    """
    combined = f"{session.get('title', '')} {session.get('description', '')} {text}".lower()

    # Look for dates in the record
    date_matches = re.findall(r"\b(\d{1,2}[./-]\d{1,2}[./-]\d{2,4}|\d{4})\b", combined)
    earliest_year = None
    for dm in date_matches:
        try:
            if len(dm) == 4 and dm.isdigit():
                yr = int(dm)
                if 1950 <= yr <= 2030:
                    earliest_year = min(earliest_year, yr) if earliest_year else yr
            else:
                parts = re.split(r"[./-]", dm)
                if len(parts) == 3 and len(parts[-1]) in (2, 4):
                    yr = int(parts[-1]) if len(parts[-1]) == 4 else (2000 + int(parts[-1]))
                    if 1950 <= yr <= 2030:
                        earliest_year = min(earliest_year, yr) if earliest_year else yr
        except Exception:
            pass

    # Check explicit statute references in input
    mentions_bns = "bns" in combined or "bharatiya nyaya" in combined or "bnss" in combined
    mentions_ipc = "ipc" in combined or "indian penal code" in combined or "crpc" in combined

    if mentions_bns and not mentions_ipc:
        era = "BNS_BNSS"
        statute_title = "Bharatiya Nyaya Sanhita, 2023 & BNSS, 2023"
        transition_note = "Offence and proceedings initiated under the Bharatiya Nyaya Sanhita, 2023 and Bharatiya Nagarik Suraksha Sanhita, 2023."
    elif earliest_year and earliest_year >= 2025:
        era = "BNS_BNSS"
        statute_title = "Bharatiya Nyaya Sanhita, 2023 & BNSS, 2023"
        transition_note = "Offence date falls on or after 1 July 2024. Substantive liability governed by BNS 2023."
    else:
        era = "IPC_CRPC"
        statute_title = "Indian Penal Code, 1860 & Code of Criminal Procedure, 1973"
        transition_note = (
            "Substantive offences committed prior to 1 July 2024 are strictly governed by IPC, 1860 under Article 20(1) of the Constitution. "
            "Under Section 531(2)(a) BNSS, 2023, pending inquiries, trials, appeals, and applications continue under the Code of Criminal Procedure, 1973."
        )

    return {
        "era": era,
        "statute_title": statute_title,
        "transition_note": transition_note,
        "cross_walk": PROVISION_CROSS_WALK
    }


def analyze_procedural_context(session: Dict[str, Any], chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyzes the complete judicial forum, procedural posture, party designations,
    and stage-appropriate legal next steps.
    """
    title = session.get("title", "")
    desc = session.get("description", "")
    user_pos = session.get("user_position", "appellant").strip().lower()
    court_raw = session.get("court", "").strip()

    combined_text = f"{title} {desc} {court_raw} " + " ".join([c.get("text", "") for c in chunks[:5]])
    combined_lower = combined_text.lower()

    # 1. Forum Determination
    is_sc = any(term in combined_lower for term in [
        "supreme court", "apex court", "special leave petition", "slp (crl)", "slp(crl)", "insc", "scc"
    ]) or "supreme court" in court_raw.lower()

    is_hc = any(term in combined_lower for term in [
        "high court", "principal seat", "nagpur bench", "lucknow bench", "criminal appeal", "crla"
    ]) and not is_sc

    # 2. Case Posture Determination (Concluded vs Pending)
    is_decided = any(term in combined_lower for term in [
        "decided on", "conviction altered", "allowed in part", "dismissed on", "judgment dated",
        "sentenced to period undergone", "disposed of", "held that", "quashed the proceedings", "order dated"
    ])

    is_arrest_safeguards = any(term in combined_lower for term in [
        "41a", "41 crpc", "35 bnss", "notice of appearance", "mechanical arrest", "498a", "85 bns", "illegal arrest", "safeguards against arrest"
    ])

    # 3. Party Parsing
    parties = re.split(r"\s+(?:v\.|vs\.|v/s|versus)\s+", title, flags=re.IGNORECASE)
    if len(parties) >= 2:
        appellant = parties[0].strip()
        respondent = parties[1].strip()
    elif len(parties) == 1 and parties[0].strip():
        appellant = parties[0].strip()
        respondent = session.get("opposing_party") or "Respondent State / Opposing Party"
    else:
        appellant = "Appellant / Applicant"
        respondent = session.get("opposing_party") or "Respondent State / Opposing Party"

    party_role = "Appellant" if user_pos in ("appellant", "petitioner", "applicant", "accused") else "Respondent"

    # 4. Prior Procedural History Extraction
    prior_stages = []
    lines = [s.strip() for s in re.split(r"[.\n]+", desc) if len(s.strip()) > 15]
    for line in lines:
        line_l = line.lower()
        if any(term in line_l for term in ["sessions", "trial court", "additional sessions", "convicted by", "magistrate", "sessions case"]):
            prior_stages.append(f"Trial Stage: {line}")
        elif any(term in line_l for term in ["high court", "first appeal", "appeal dismissed", "confirmed the conviction"]):
            prior_stages.append(f"High Court Stage: {line}")
        elif any(term in line_l for term in ["supreme court", "slp", "criminal appeal no", "apex court"]):
            prior_stages.append(f"Supreme Court Stage: {line}")

    if not prior_stages:
        if is_sc:
            prior_stages = [
                "Trial Court – Conviction and sentence by Sessions Court",
                "High Court – First appellate review under Section 374 CrPC",
                "Supreme Court of India – Apex appellate adjudication"
            ]
        elif is_hc:
            prior_stages = [
                "Trial Court – Conviction and sentence by Sessions Court",
                f"{court_raw or 'High Court'} – Appellate jurisdiction under Section 374 CrPC"
            ]
        else:
            prior_stages = [f"{court_raw or 'Trial Court'} – Original jurisdiction / Trial"]

    # 5. Forum & Posture Assembly with Stage-Appropriate Next Steps
    statutory_info = evaluate_statutory_era(session, combined_text)

    if is_sc:
        current_forum = "Supreme Court of India"
        posture = "Decided Criminal Appeal" if is_decided else "Criminal Appellate Proceeding (Supreme Court of India)"
        if is_decided:
            next_steps = (
                "1. Formal Transmission: Transmit certified copy of Supreme Court judgment to Trial Court and Jail Superintendent.\n"
                "2. Sentence Set-off Verification: Verify detention period undergone under Section 428 CrPC / Section 468 BNSS against the modified sentence.\n"
                "3. Immediate Release Execution: If detention period meets or exceeds modified term of imprisonment, move application for formal release from custody.\n"
                "4. Procedural Integrity Note: No rejoinder, fresh writ petition, or High Court appeal is maintainable since the Supreme Court has rendered its conclusive final judgment."
            )
        else:
            next_steps = (
                "1. Paper Book Compilation: Compile official paper books citing lower court record and statutory exhibits.\n"
                "2. Precedent Dossier: Submit compilation of binding Supreme Court authorities.\n"
                "3. Oral Submissions: Advance arguments demonstrating absence of premeditation or statutory defense."
            )
    elif is_hc:
        current_forum = court_raw or "High Court of Judicature"
        posture = "Decided High Court Appeal" if is_decided else "Criminal Appeal under Section 374(2) CrPC"
        if is_decided:
            next_steps = (
                "1. Special Leave Petition: Prepare Special Leave Petition (Criminal) before Supreme Court of India under Article 136 within the 90-day limitation.\n"
                "2. Certified Copies: Apply immediately for certified copies of the High Court judgment.\n"
                "3. Suspension of Sentence: Move application for suspension of sentence pending SLP under Section 389 CrPC."
            )
        elif is_arrest_safeguards:
            next_steps = (
                "1. Contempt Application: Initiate contempt proceedings under Contempt of Courts Act against Investigating Officer for non-compliance with statutory notice of appearance mandates under Section 41A CrPC / Section 35(3) BNSS.\n"
                "2. Interim Protection: Pray for stay of coercive steps under Section 482 CrPC / Section 528 BNSS.\n"
                "3. Departmental Notice: Issue statutory representation to Commissioner/SP citing mandatory guidelines."
            )
        else:
            next_steps = (
                "1. Paper Books: Ensure paper books and translated lower court depositions are filed.\n"
                "2. Oral Hearing: Press arguments on material contradictions and misapplication of legal principles.\n"
                "3. Rejoinder / Reply: File rejoinder affidavit only if specifically permitted or directed by the Court."
            )
    else:
        current_forum = court_raw or "Trial Court / Sessions Court"
        posture = "Trial / Original Proceeding"
        if is_arrest_safeguards:
            next_steps = (
                "1. Section 41A Notice Scrutiny: Challenge mechanical arrest before Magistrate citing mandatory statutory safeguards governing arrest without warrant under Section 41 CrPC / Section 35 BNSS.\n"
                "2. Bail Application: Move application under Section 437/439 CrPC on ground of non-compliance with arrest safeguards.\n"
                "3. Magisterial Satisfaction Note: Demand recording of reasons by Magistrate under Section 41(1)(b)(ii) CrPC before authorizing detention."
            )
        else:
            next_steps = (
                "1. Statutory Statement: Submit written explanation under Section 313(5) CrPC / Section 351(5) BNSS detailing defense case.\n"
                "2. Cross-Examination: Cross-examine prosecution witnesses on material omissions and absence of premeditation.\n"
                "3. Defense Evidence: Tender defense witnesses or documentary exhibits under Section 233 CrPC if warranted."
            )

    return {
        "current_forum": current_forum,
        "posture": posture,
        "appellant": appellant,
        "respondent": respondent,
        "party_role": party_role,
        "prior_stages": prior_stages,
        "is_decided": is_decided,
        "is_arrest_safeguards": is_arrest_safeguards,
        "statutory_era": statutory_info["era"],
        "statute_title": statutory_info["statute_title"],
        "transition_note": statutory_info["transition_note"],
        "next_steps": next_steps,
    }
