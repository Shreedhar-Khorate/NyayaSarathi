"""
Pytest configuration and shared fixtures for NyayaSarathi backend test suite.
Provides automated LLM mocking for legal drafting tests to ensure zero external API calls,
zero test flakiness, and deterministic test execution in milliseconds.
"""

import re
import pytest
from unittest.mock import patch


@pytest.fixture(autouse=True)
def mock_drafting_llm_fallback():
    """
    Autouse fixture that mocks LLM calls for drafting tests when an explicit mock is not provided.
    Yields to let tests override _call_llm_json when testing specific failure modes.
    """
    def fake_llm(system_prompt: str, user_prompt: str):
        is_mr = "TARGET LANGUAGE: mr" in user_prompt
        is_hi = "TARGET LANGUAGE: hi" in user_prompt

        if "SECTION TO REGENERATE" in user_prompt:
            return {
                "content": "Special medical grounds: Applicant suffers from severe acute cardiac illness requiring specialized medical attention outside custody."
            }, "groq", "test-model", 10, 10

        if "DOCUMENT TYPE: legal_notice" in user_prompt:
            if is_mr:
                title = "कायदेशीर नोटीस (LEGAL NOTICE)"
                sections = [
                    {"id": "sec_1", "title": "नोटीस प्रेषक व प्राप्तकर्ता तपशील", "content": "प्रति, मे. एक्सवायझेड प्रा. लि., पत्ता: पुणे, महाराष्ट्र. माझे अशील यांच्या सूचनेनुसार.", "order": 1},
                    {"id": "sec_2", "title": "प्रकरणातील वस्तुस्थिती व व्यवहार", "content": "करारानुसार मालाचा पुरवठा केला असून रक्कम बाकी आहे.", "order": 2},
                    {"id": "sec_3", "title": "कायदेशीर कारणे व तरतुदी", "content": "भारतीय करार कायदा कलम ७३ अंतर्गत कायदेशीर जबाबदारी.", "order": 3},
                    {"id": "sec_4", "title": "अंतिम मागणी व कायदेशीर कारवाईचा इशारा", "content": "१५ दिवसांत थकबाकी अदा करावी अन्यथा न्यायालयात दावा दाखल केला जाईल.", "order": 4},
                ]
            elif is_hi:
                title = "विधिक सूचना (LEGAL NOTICE)"
                sections = [
                    {"id": "sec_1", "title": "विधिक सूचना प्रेषण विवरण", "content": "सेवा में, विपक्षी। मुवक्किल के स्पष्ट निर्देशानुसार यह विधिक नोटिस प्रेषित है।", "order": 1},
                    {"id": "sec_2", "title": "तथ्यों का विस्तृत विवरण", "content": "संविदा के अनुसार भुगतान बकाया है।", "order": 2},
                    {"id": "sec_3", "title": "कानूनी आधार", "content": "भारतीय संविदा अधिनियम धारा 73 के तहत देयता।", "order": 3},
                    {"id": "sec_4", "title": "अंतिम मांग एवं कानूनी चेतावनी", "content": "15 दिनों में बकाया राशि का भुगतान करें।", "order": 4},
                ]
            else:
                title = "LEGAL NOTICE DEMANDING ARREARS"
                sections = [
                    {"id": "sec_1", "title": "Header & Particulars", "content": "Served on behalf of Apex Manufacturing Ltd. to ABC Enterprises.", "order": 1},
                    {"id": "sec_2", "title": "Chronological Material Facts", "content": "Contract for industrial valves and default of Rs. 4,50,000/-.", "order": 2},
                    {"id": "sec_3", "title": "Statutory Grounds of Liability", "content": "Section 73 Indian Contract Act, 1872.", "order": 3},
                    {"id": "sec_4", "title": "Peremptory Demand for Payment", "content": "Immediate payment of Rs. 4,50,000/- within notice period.", "order": 4},
                ]
            cits = [{"title": "Section 73, Indian Contract Act, 1872", "citation": "Indian Contract Act §73"}]

        elif "DOCUMENT TYPE: bail_application" in user_prompt:
            if is_mr:
                title = "फौजदारी नियमित जामीन अर्ज (REGULAR BAIL APPLICATION)"
                sections = [
                    {
                        "id": "sec_1",
                        "title": "मा. न्यायालय व पक्षकार",
                        "content": "मेहेरबान मा. सत्र न्यायालय, पुणे.\nफौजदारी नियमित जामीन अर्ज\nअर्जदार / आरोपी: विजय साळुंखे\nविरुद्ध\nगैरअर्जदार / सरकार: महाराष्ट्र शासन.",
                        "order": 1,
                    },
                    {
                        "id": "sec_2",
                        "title": "तथ्ये व कोठडी तपशील",
                        "content": "अर्जदार येरवडा कारागृहात न्यायालयीन कोठडीत आहेत. एफआयआर क्र. 99/2024 शिवाजीनगर पोलीस स्टेशन. कलम 318(4) बीएनएस.",
                        "order": 2,
                    },
                    {
                        "id": "sec_3",
                        "title": "जामिनाची कारणे",
                        "content": "सदरहू प्रकरणात जामिनाची कारणे: भारतीय नागरिक सुरक्षा संहिता, २०२३ चे कलम ४८३ अन्वये जामीन अर्ज. अर्जदार कायमस्वरूपी रहिवासी असून पुरावा नष्ट करण्याचा कोणताही धोका नाही.",
                        "order": 3,
                    },
                    {
                        "id": "sec_4",
                        "title": "प्रार्थना व हमीपत्र",
                        "content": "अर्जदारास नियमित जामीन मंजूर करावा. जोडपत्रांची यादी व सत्यप्रतिज्ञा सोबत जोडली आहे.",
                        "order": 4,
                    },
                ]
                cits = [{"title": "भारतीय नागरिक सुरक्षा संहिता, २०२३ चे कलम ४८३", "citation": "कलम ४८३ बीएनएसएस"}]
            else:
                # English Bail - resolve procedural section based on jurisdiction / relief
                jurisdiction_match = re.search(r"JURISDICTION / COURT:\s*([^\n]+)", user_prompt)
                jurisdiction_text = jurisdiction_match.group(1).lower() if jurisdiction_match else ""
                relief_match = re.search(r"RELIEF REQUESTED:\s*([^\n]+)", user_prompt)
                relief_text = relief_match.group(1).lower() if relief_match else ""

                is_anticipatory = "anticipatory" in user_prompt.lower() or "anticipatory" in relief_text
                is_magistrate = bool(re.search(r"\b(magistrate|jmfc|cjm|mm\b|cmm\b|acmm\b|judicial\s*magistrate|metropolitan\s*magistrate)\b", jurisdiction_text))

                if is_anticipatory:
                    bail_sec = "Section 482"
                    bail_sec_title = "Section 482 of the Bharatiya Nagarik Suraksha Sanhita, 2023"
                elif is_magistrate:
                    bail_sec = "Section 480"
                    bail_sec_title = "Section 480 of the Bharatiya Nagarik Suraksha Sanhita, 2023"
                else:
                    bail_sec = "Section 483"
                    bail_sec_title = "Section 483 of the Bharatiya Nagarik Suraksha Sanhita, 2023"

                # Check if offence sections were provided
                offence_sec_str = ""
                if "APPLICABLE SECTIONS: ['Section 303(2) BNS" in user_prompt or "303(2)" in user_prompt:
                    offence_sec_str = "Section 303(2) BNS"
                elif "APPLICABLE SECTIONS: ['Section 318(4) BNS" in user_prompt or "318(4)" in user_prompt:
                    offence_sec_str = "Section 318(4) BNS, 2023"
                else:
                    offence_sec_str = "[INFORMATION REQUIRED: Offence sections under BNS/IPC]"

                title = f"CRIMINAL BAIL APPLICATION UNDER {bail_sec.upper()}"
                sections = [
                    {
                        "id": "sec_1",
                        "title": "Court & Cause Title",
                        "content": (
                            "IN THE COURT OF SESSION / COMPETENT JURISDICTION\n"
                            "BAIL APPLICATION NO. [TBD] OF 2024\n"
                            "IN THE MATTER OF:\n"
                            "APPLICANT / ACCUSED\n"
                            "VERSUS\n"
                            "RESPONDENT / STATE / PROSECUTION\n"
                            f"CRIMINAL REGULAR BAIL APPLICATION UNDER {bail_sec_title}"
                        ),
                        "order": 1,
                    },
                    {
                        "id": "sec_2",
                        "title": "FIR and Custody Chronology",
                        "content": (
                            f"FIR No. 201/2024 registered at Bandra Police Station under {offence_sec_str}.\n"
                            "CHRONOLOGY OF MATERIAL EVENTS & FACTS:\n"
                            "The applicant was arrested on 05.08.2024 / 10.08.2024.\n"
                            "ARREST PARTICULARS AND CUSTODIAL STATUS: Currently in judicial custody.\n"
                            "PARTICULARS OF PREVIOUS BAIL APPLICATIONS: No previous application preferred."
                        ),
                        "order": 2,
                    },
                    {
                        "id": "sec_3",
                        "title": "Grounds for Bail",
                        "content": (
                            "SUBSTANTIVE GROUNDS FOR GRANT OF BAIL:\n"
                            "1. The applicant respectfully contends that he has been falsely implicated in the present case.\n"
                            "2. [INFORMATION REQUIRED: Criminal antecedents of applicant].\n"
                            "3. [INFORMATION REQUIRED: Family dependency and deep roots in society].\n"
                            "4. [INFORMATION REQUIRED: Interrogation status] [MISSING: Police Station details].\n"
                            "5. [INFORMATION REQUIRED: Recovery status].\n"
                            "STATUTORY PROVISION AND PRECEDENTS: Governed by personal liberty standards under Article 21."
                        ),
                        "order": 3,
                    },
                    {
                        "id": "sec_4",
                        "title": "Statutory Provisions and Precedents",
                        "content": (
                            f"STATUTORY PROVISION AND PRECEDENTS: Governed by {bail_sec_title} and personal liberty standards under Article 21."
                        ),
                        "order": 4,
                    },
                    {
                        "id": "sec_5",
                        "title": "Prayer for Relief",
                        "content": (
                            "PRAYER FOR RELIEF:\n"
                            f"It is most respectfully prayed that the applicant be enlarged on regular bail under {bail_sec}.\n"
                            "PROPOSED BAIL CONDITIONS: Applicant undertakes to abide by all conditions and furnish solvent surety.\n"
                            "VERIFICATION & AFFIDAVIT IN SUPPORT\n"
                            "LIST OF ANNEXURES: Annexure A1."
                        ),
                        "order": 5,
                    },
                ]
                cits = [{"title": bail_sec_title, "citation": f"{bail_sec} BNSS"}]

        elif "DOCUMENT TYPE: petition" in user_prompt:
            title = "WRIT PETITION UNDER ARTICLE 226"
            sections = [
                {"id": "sec_1", "title": "Cause Title & Jurisdiction", "content": "In the High Court of Bombay. Dr. Sunil Patil vs MCGM.", "order": 1},
                {"id": "sec_2", "title": "Synopsis & Chronology of Material Facts", "content": "Pharmacy premises arbitrarily sealed without notice on 12.02.2024.", "order": 2},
                {"id": "sec_3", "title": "Specific Grounds of Challenge", "content": "Grounds of violation of natural justice.", "order": 3},
                {"id": "sec_4", "title": "Main Prayers & Interim Relief", "content": "Writ of Certiorari quashing the sealing order.", "order": 4},
            ]
            cits = [{"title": "Article 226, Constitution of India", "citation": "Constitution of India Art. 226"}]

        elif "DOCUMENT TYPE: reply" in user_prompt:
            title = "WRITTEN STATEMENT & FORMAL REPLY"
            sections = [
                {"id": "sec_1", "title": "Preliminary Objections", "content": "Notice is unfounded and without actionable cause of action.", "order": 1},
                {"id": "sec_2", "title": "Para-wise Response to Material Facts", "content": "Goods were tendered on time; delay is solely on claimant.", "order": 2},
                {"id": "sec_3", "title": "Affirmative Defense & Counter-Grounds", "content": "Storage demurrage charges incurred due to claimant's delay.", "order": 3},
                {"id": "sec_4", "title": "Rejection of Demands & Verification", "content": "Baseless demands rejected. Verified by counsel.", "order": 4},
            ]
            cits = [{"title": "Order VIII Rules 3-5, Code of Civil Procedure, 1908", "citation": "CPC Order VIII"}]

        else:
            title = "STRUCTURED LEGAL DRAFT"
            sections = [
                {"id": "sec_1", "title": "Pleadings Header", "content": "Parties and forum details.", "order": 1},
                {"id": "sec_2", "title": "Statement of Facts", "content": "Chronology of events.", "order": 2},
                {"id": "sec_3", "title": "Substantive Legal Grounds", "content": "Statutory grounds.", "order": 3},
                {"id": "sec_4", "title": "Prayer for Relief", "content": "Specific relief sought.", "order": 4},
            ]
            cits = []

        full_text = f"{title}\n\n" + "\n\n".join(f"## {s['title']}\n{s['content']}" for s in sections)
        return {
            "title": title,
            "sections": sections,
            "full_draft_text": full_text,
            "citations": cits,
        }, "groq", "test-model", 100, 100

    with patch("services.drafts_service._call_llm_json", side_effect=fake_llm) as p:
        yield p


@pytest.fixture(autouse=True)
def mock_war_room_llm():
    """
    Autouse fixture that mocks LLM calls for war room tests to ensure zero external API calls,
    protection against Groq 429 rate limits, and deterministic test execution in milliseconds.
    """
    def fake_war_room_llm(system_prompt: str, user_prompt: str):
        is_civil = "Civil" in system_prompt or "property" in user_prompt.lower()
        
        # Check operation type from system_prompt / user_prompt
        if "draft rigorous legal arguments" in system_prompt.lower() or "affirmative argument" in system_prompt.lower():
            provisions = ["Section 54 Transfer of Property Act", "Section 17 Registration Act"] if is_civil else ["Section 438 CrPC", "Section 41A CrPC"]
            return [
                {
                    "id": "arg-1",
                    "title": "Presumption of Registered Ownership" if is_civil else "Protection Against Mechanical Arrest",
                    "legal_issue": "Whether registered title prevails over oral settlement" if is_civil else "Whether arrest notice under Section 41A CrPC is mandatory",
                    "applicable_provisions": provisions,
                    "main_claim": "Registered instrument confers absolute right in immovable property." if is_civil else "Custodial arrest cannot be effected without compliance with Section 41A CrPC.",
                    "supporting_facts": ["Registered sale deed executed in 2019" if is_civil else "Clean antecedents and civil nature of dispute"],
                    "evidence_actually_available": ["Copy of registered sale deed" if is_civil else "Notice under Section 41A CrPC"],
                    "evidence_refs": ["Copy of registered sale deed" if is_civil else "Notice under Section 41A CrPC"],
                    "evidence_still_required": ["Certified copy from Sub-Registrar" if is_civil else "Case diary entries"],
                    "relevant_precedents": ["Suraj Lamp & Industries v. State of Haryana" if is_civil else "Arnesh Kumar v. State of Bihar"],
                    "confidence_status": "High Doctrinal Ground"
                }
            ], "groq(mock)", "test-model", 50, 50

        elif "case overview" in system_prompt.lower() or "case summary" in system_prompt.lower():
            return {
                "case_summary": "Dispute concerning ownership of residential property under registered sale deed (2019) vs oral family settlement (2021).",
                "important_facts": [
                    {"id": 1, "fact": "Registered sale deed executed in 2019", "category": "documentary_evidence"},
                    {"id": 2, "fact": "Occupation commenced in 2021", "category": "party_allegation"}
                ],
                "unverified_allegations": [],
                "main_legal_issues": [
                    "Validity of title under Transfer of Property Act 1882",
                    "Admissibility of unregistered family settlement under Registration Act 1908"
                ],
                "relevant_dates": [
                    {"event_date": "2019", "description": "Execution of registered sale deed in 2019"},
                    {"event_date": "2021", "description": "Commencement of occupation in 2021"}
                ]
            }, "groq(mock)", "test-model", 50, 50

        elif "fact sheet" in system_prompt.lower() or "factual finding" in system_prompt.lower():
            return [
                {"id": 1, "fact": "State of Maharashtra v. Rajesh Sharma", "category": "procedural_event"},
                {"id": 2, "fact": "Applicant seeks anticipatory bail under Section 438 CrPC", "category": "party_allegation"}
            ], "groq(mock)", "test-model", 50, 50

        elif "opposing party" in system_prompt.lower() or "devil's advocate" in system_prompt.lower() or "opposition" in system_prompt.lower() or "hostile" in system_prompt.lower():
            return [
                {
                    "id": "opp-1",
                    "opposing_claim": "Claimant holds prior rights under family settlement",
                    "adverse_precedents": ["Kale v. Deputy Director of Consolidation"],
                    "suggested_rebuttal_counterarguments": ["Unregistered settlement creating right in immovable property requires registration under Section 17 Registration Act."],
                    "user_position_weaknesses": ["Primary custody of original settlement document."]
                }
            ], "groq(mock)", "test-model", 50, 50

        elif "evidence specialist" in system_prompt.lower() or "evidentiary" in system_prompt.lower() or "evidence" in system_prompt.lower():
            return [
                {
                    "id": "ev-1",
                    "exhibit_name": "Sale Deed Copy",
                    "finding": "Photocopy of registered sale deed executed in 2019",
                    "reliability": "secondary_evidence",
                    "why_it_matters": "Requires production of certified copy or original under Section 65 Evidence Act."
                }
            ], "groq(mock)", "test-model", 50, 50

        elif "risk" in system_prompt.lower():
            return [
                {
                    "id": "risk-1",
                    "risk_type": "missing_evidence",
                    "description": "Original title documents not produced in primary pleadings.",
                    "severity": "medium"
                }
            ], "groq(mock)", "test-model", 50, 50

        elif "10-section" in system_prompt.lower() or "strategy report" in system_prompt.lower():
            return {
                "executive_summary": "Comprehensive legal strategy synthesized across primary pleadings, evidence matrix, and verified authorities.",
                "disclaimer": "This report provides strategic legal analysis and does not constitute a formal legal opinion.",
                "procedural_posture": "Active Proceedings",
                "affirmative_arguments": "Registered document carries statutory presumption of valid execution.",
                "counterarguments": "Opponent contends family arrangement prevails.",
                "precedent_landscape": "Binding judicial authorities on immovable property transfer.",
                "practical_next_steps": "File application for production of original documents."
            }, "groq(mock)", "test-model", 50, 50

        else: # Default: arguments
            provisions = ["Section 54 Transfer of Property Act", "Section 17 Registration Act"] if is_civil else ["Section 438 CrPC", "Section 41A CrPC"]
            return [
                {
                    "id": "arg-1",
                    "title": "Presumption of Registered Ownership",
                    "legal_issue": "Whether registered title prevails over oral settlement",
                    "applicable_provisions": provisions,
                    "main_claim": "Registered instrument confers absolute right in immovable property.",
                    "supporting_facts": ["Registered sale deed executed in 2019"],
                    "evidence_actually_available": ["Copy of registered sale deed"],
                    "evidence_refs": ["Copy of registered sale deed"],
                    "evidence_still_required": ["Certified copy from Sub-Registrar"],
                    "relevant_precedents": ["Suraj Lamp & Industries v. State of Haryana"],
                    "confidence_status": "High Doctrinal Ground"
                }
            ], "groq(mock)", "test-model", 50, 50

    with patch("services.war_room_service._call_llm_json", side_effect=fake_war_room_llm) as p:
        yield p
