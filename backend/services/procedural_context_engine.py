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
    case_type = session.get("case_type", "").lower()

    # Civil dispute check
    is_civil_dispute = (
        case_type in ("civil", "property", "contract", "commercial", "family", "recovery") or
        any(k in combined for k in [
            "sale deed", "family settlement", "title suit", "specific relief",
            "registration act", "transfer of property", "residential property",
            "property tax receipts", "partition", "adverse possession"
        ])
    ) and not any(k in combined for k in [
        "ipc", "crpc", "bns", "bnss", "fir", "police", "bail", "murder",
        "302", "498a", "remand", "sessions case", "charge sheet", "accused"
    ])

    if is_civil_dispute:
        era = "CIVIL_STATUTES"
        statute_title = "Transfer of Property Act, 1882; Indian Registration Act, 1908; Indian Evidence Act, 1872 & Code of Civil Procedure, 1908"
        transition_note = (
            "Substantive rights and conveyances are governed by the Transfer of Property Act, 1882 and Indian Registration Act, 1908. "
            "Adjudication and pleadings are governed by the Code of Civil Procedure, 1908. For documentary and secondary evidence, the Indian Evidence Act, 1872 applies (and Bharatiya Sakshya Adhiniyam, 2023 for evidence tendered after 1 July 2024)."
        )
    elif mentions_bns and not mentions_ipc:
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
    }


def analyze_procedural_context(session: Dict[str, Any], chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyzes the complete judicial forum, procedural posture, party designations,
    and stage-appropriate legal next steps. Distinguishes civil property suits from criminal proceedings.
    """
    title = session.get("title", "")
    desc = session.get("description", "")
    user_pos = session.get("user_position", "appellant").strip().lower()
    court_raw = session.get("court", "").strip()
    case_type = session.get("case_type", "general").strip().lower()

    combined_text = f"{title} {desc} {court_raw} " + " ".join([c.get("text", "") for c in chunks[:5]])
    combined_lower = combined_text.lower()

    # Detect civil dispute
    is_civil = (
        case_type in ("civil", "property", "contract", "commercial", "family", "recovery") or
        any(k in combined_lower for k in [
            "sale deed", "family settlement", "title suit", "specific relief",
            "registration act", "transfer of property", "residential property",
            "property tax receipts", "partition", "adverse possession", "ownership"
        ])
    ) and not any(k in combined_lower for k in [
        "ipc", "crpc", "bns", "bnss", "fir", "police", "bail", "murder",
        "302", "498a", "remand", "sessions case", "charge sheet", "accused"
    ])

    # 1. Forum Determination
    is_sc = any(term in combined_lower for term in [
        "supreme court", "apex court", "special leave petition", "slp (crl)", "slp(crl)", "slp (civil)", "insc", "scc"
    ]) or "supreme court" in court_raw.lower()

    is_hc = any(term in combined_lower for term in [
        "high court", "principal seat", "nagpur bench", "lucknow bench", "criminal appeal", "crla", "first appeal", "second appeal"
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
        respondent = session.get("opposing_party") or ("Defendant / Opposing Party" if is_civil else "Respondent State / Opposing Party")
    else:
        appellant = "Plaintiff / Claimant" if is_civil else "Appellant / Applicant"
        respondent = session.get("opposing_party") or ("Defendant / Opposing Party" if is_civil else "Respondent State / Opposing Party")

    # Consistent role assignment based on user position and dispute nature
    if user_pos in ("plaintiff", "claimant"):
        party_role = "Plaintiff / Claimant"
    elif user_pos in ("defendant", "respondent"):
        party_role = "Defendant / Opposing Party" if is_civil else "Respondent"
    elif user_pos in ("appellant", "petitioner", "applicant", "accused"):
        party_role = "Appellant"
    else:
        party_role = "Plaintiff / Claimant" if is_civil else "Appellant"

    # 4. Prior Procedural History Extraction
    prior_stages = []
    lines = [s.strip() for s in re.split(r"[.\n]+", desc) if len(s.strip()) > 15]
    for line in lines:
        line_l = line.lower()
        if any(term in line_l for term in ["sessions", "trial court", "additional sessions", "convicted by", "magistrate", "sessions case", "civil judge", "sub-judge"]):
            prior_stages.append(f"Trial Stage: {line}")
        elif any(term in line_l for term in ["high court", "first appeal", "appeal dismissed", "confirmed the conviction"]):
            prior_stages.append(f"High Court Stage: {line}")
        elif any(term in line_l for term in ["supreme court", "slp", "criminal appeal no", "civil appeal no", "apex court"]):
            prior_stages.append(f"Supreme Court Stage: {line}")

    if not prior_stages:
        if is_civil:
            if is_sc:
                prior_stages = [
                    "Trial Court – Original Civil Suit (Declaration and Title)",
                    "High Court – First/Second Appellate Review",
                    "Supreme Court of India – Apex appellate adjudication"
                ]
            elif is_hc:
                prior_stages = [
                    "Trial Court – Original Civil Suit before Civil Judge / District Court",
                    f"{court_raw or 'High Court'} – Regular First Appeal under Section 96 CPC"
                ]
            else:
                prior_stages = [f"{court_raw or 'Civil Court'} – Original jurisdiction / Pre-institution title dispute"]
        else:
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

    if is_civil:
        if is_sc:
            current_forum = "Supreme Court of India"
            posture = "Decided Civil Appeal" if is_decided else "Civil Appellate Proceeding (Supreme Court of India)"
            next_steps = (
                "1. Decree Transmission: Transmit certified copy of Supreme Court judgment and decree to Trial Court for execution.\n"
                "2. Execution Petition: File execution petition under Order XXI CPC before executing court to enforce declaration/possession.\n"
                "3. Conclusive Finality: No further appeal lies against Supreme Court judgment."
            )
        elif is_hc:
            current_forum = court_raw or "High Court of Judicature"
            posture = "Decided Civil Appeal" if is_decided else "Regular Civil Appeal / Civil Revision (High Court)"
            next_steps = (
                "1. Regular First Appeal: File Regular First Appeal under Section 96 CPC within the 90-day statutory limitation.\n"
                "2. Stay of Execution: Move application under Order XLI Rule 5 CPC for stay of trial court judgment/decree.\n"
                "3. Certified Copies: Apply immediately for certified copies of the trial court judgment and decree."
            )
        else:
            current_forum = court_raw or "Civil Court / Court of Civil Judge (Senior Division)"
            posture = "Original Civil Suit / Title Dispute"
            next_steps = (
                "1. Production of Primary Documents: File certified copies of title deeds, revenue extracts, and primary instruments relied upon under Order VII Rule 14 CPC.\n"
                "2. Admissibility & Evidentiary Scrutiny: Scrutinize adverse documents for execution, attestation, and mandatory registration requirements under Sections 17 & 49 of the Indian Registration Act, 1908 and the Evidence Act / BSA.\n"
                "3. Plaint Formulation: Draft civil plaint for Declaration of Title, Recovery of Possession, and Ancillary Relief under the Specific Relief Act, 1963 and Order VII CPC.\n"
                "4. Interlocutory Injunction: Move application under Order XXXIX Rules 1 & 2 CPC restraining the adverse party from creating third-party interests, alienating the property, or altering its physical status."
            )
    elif is_sc:
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
        "is_civil": is_civil,
        "is_arrest_safeguards": is_arrest_safeguards,
        "statutory_era": statutory_info["era"],
        "statute_title": statutory_info["statute_title"],
        "transition_note": statutory_info["transition_note"],
        "next_steps": next_steps,
    }
