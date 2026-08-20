"""
Case Understanding and Classification Engine for NyayaSarathi.

Responsible for:
1. Indian Statutory & Legal Entity Extraction (Acts, Sections, Articles, Courts).
2. Multi-Class Indian Case Classification across 16+ legal domains.
3. User Position / Role Detection (Petitioner, Respondent, Appellant, etc.).
4. Fact & Legal Issue Extraction.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from models.prediction import StructuredCaseProfile


# ── INDIAN ACT KNOWLEDGE BASE ───────────────────────────────────────────
ACT_PATTERNS = {
    "Code of Criminal Procedure": [
        r"\b(?:cr\.?p\.?c\.?|code of criminal procedure|bnss|bharatiya nagarik suraksha sanhita)\b",
        r"\bsection\s*(?:438|439|482|154|156|164|167|173|200|311|313|374|378|397|401)\b",
    ],
    "Indian Penal Code / Bharatiya Nyaya Sanhita": [
        r"\b(?:i\.?p\.?c\.?|indian penal code|bns|bharatiya nyaya sanhita)\b",
        r"\bsection\s*(?:302|304|304a|306|307|323|325|354|376|379|380|384|406|409|419|420|467|468|471|498a|506|120b)\b",
    ],
    "Code of Civil Procedure": [
        r"\b(?:c\.?p\.?c\.?|code of civil procedure|order\s*(?:xxxix|39|vii|7|viii|8|xxi|21))\b",
        r"\bsection\s*(?:9|10|11|100|115|151)\s*(?:c\.?p\.?c\.?|code of civil procedure)?\b",
    ],
    "Indian Contract Act, 1872": [
        r"\b(?:contract act|indian contract act|breach of contract|liquidated damages|quantum meruit)\b",
        r"\bsection\s*(?:73|74|75|10|23|27|56)\s*(?:contract act)?\b",
    ],
    "Negotiable Instruments Act, 1881": [
        r"\b(?:n\.?i\.?\s*act|negotiable instruments act|cheque bounce|dishonou?r of cheque|statutory notice)\b",
        r"\bsection\s*(?:138|139|141|142)\b",
    ],
    "Motor Vehicles Act, 1988": [
        r"\b(?:motor vehicles act|m\.?v\.?\s*act|mact|motor accident|vehicular accident|third party insurance|compensation for death|permanent disability)\b",
        r"\bsection\s*(?:166|163a|140|149|173)\s*(?:m\.?v\.?\s*act|motor vehicles act)?\b",
    ],
    "Constitution of India": [
        r"\b(?:constitution of india|fundamental rights?|writ of (?:mandamus|certiorari|habeas corpus|quowarranto|prohibition))\b",
        r"\barticle\s*(?:226|227|32|136|14|19|21|300a|311)\b",
    ],
    "Specific Relief Act / Property Law": [
        r"\b(?:specific relief act|specific performance|transfer of property act|t\.?p\.?\s*act|injunction suit|suit for declaration|adverse possession|eviction)\b",
        r"\bsection\s*(?:34|38|39|41|16|20|53a|54|58)\s*(?:specific relief|transfer of property)?\b",
    ],
    "Family Courts Act / Hindu Marriage Act": [
        r"\b(?:hindu marriage act|special marriage act|family courts? act|divorce petition|restitution of conjugal|maintenance under 125|custody of child|domestic violence act|d\.?v\.?\s*act)\b",
        r"\bsection\s*(?:13|13b|9|24|25|125)\s*(?:hma|hindu marriage)?\b",
    ],
    "Arbitration and Conciliation Act, 1996": [
        r"\b(?:arbitration and conciliation act|arbitration act|arbitral tribunal|section 34 petition|section 9 interim|section 11 appointment)\b",
        r"\bsection\s*(?:9|11|34|37)\s*(?:arbitration)?\b",
    ],
    "Consumer Protection Act, 2019": [
        r"\b(?:consumer protection act|c\.?p\.?\s*act|deficiency of service|unfair trade practice|ncdrc|state consumer commission|district consumer forum)\b",
    ],
    "Income Tax Act, 1961": [
        r"\b(?:income tax act|i\.?t\.?\s*act|assessment year|itat|commissioner of income tax|c\.?i\.?t\.?|capital gains|section 148|reassessment)\b",
        r"\bsection\s*(?:147|148|143|260a)\s*(?:income tax)?\b",
    ],
    "NDPS Act / Special Acts": [
        r"\b(?:ndps act|narcotic drugs|pocso act|prevention of corruption act|p\.?c\.?\s*act|pmla|prevention of money laundering)\b",
    ],
    "Service & Labour Law": [
        r"\b(?:service matter|disciplinary proceedings|pensionary benefits|seniority list|compassionate appointment|industrial disputes act|termination of service|central administrative tribunal|cat)\b",
    ],
}


# ── DOMAIN & CASE TYPE CLASSIFICATION RULES ───────────────────────────
CATEGORY_KEYWORDS = {
    "bail": [
        "bail", "anticipatory bail", "regular bail", "custody", "incarceration",
        "section 438", "section 439", "cr. misc", "crm", "arrest", "surrender",
        "pre-arrest", "remand", "bail application", "surety", "custodial interrogation"
    ],
    "criminal_appeal": [
        "conviction", "sentence", "trial court convicted", "criminal appeal", "cra", "crl.a",
        "rigorous imprisonment", "ipc 302", "ipc 307", "acquittal challenged", "quantum of sentence"
    ],
    "criminal_revision": [
        "criminal revision", "crr", "crl.r", "section 397", "section 401", "discharge application",
        "framing of charge", "cognizance order"
    ],
    "writ_civil": [
        "writ petition", "article 226", "article 227", "w.p.(c)", "wp(c)", "mandamus",
        "certiorari", "quash government order", "tender cancellation", "administrative action"
    ],
    "writ_criminal": [
        "wp(crl)", "w.p.(crl)", "habeas corpus", "quash fir under article 226", "police atrocities",
        "fair investigation writ"
    ],
    "motor_accident": [
        "motor accident", "mact", "accident claim", "rash and negligent", "vehicular accident",
        "compensation under section 166", "insurance company liability", "multiplier method", "loss of dependency"
    ],
    "contract": [
        "breach of contract", "indian contract act", "section 73", "section 74", "damages",
        "vendor agreement", "non-performance", "termination of agreement", "invocation of bank guarantee"
    ],
    "cheque_bounce": [
        "section 138", "ni act", "negotiable instruments", "dishonour of cheque", "cheque return memo",
        "insufficient funds", "statutory notice under 138"
    ],
    "civil": [
        "civil suit", "money suit", "injunction", "order 39 cpc", "summary suit", "suit for recovery",
        "cpc section 9", "interim injunction"
    ],
    "civil_appeal": [
        "first appeal", "second appeal", "rfa", "rsa", "civil appeal", "substantial question of law",
        "appellate decree"
    ],
    "property": [
        "partition suit", "suit for declaration", "title dispute", "adverse possession",
        "transfer of property", "eviction suit", "land acquisition", "revenue records", "encroachment"
    ],
    "family": [
        "divorce", "hindu marriage act", "section 13 hma", "custody", "maintenance",
        "section 125 crpc", "domestic violence", "matrimonial dispute", "cruelty under 498a"
    ],
    "arbitration": [
        "arbitration", "arbitrator", "section 34", "section 9", "section 11", "arbitral award",
        "arbitration and conciliation"
    ],
    "consumer": [
        "consumer protection", "ncdrc", "deficiency of service", "medical negligence",
        "flat buyer", "delayed possession", "state consumer commission"
    ],
    "service": [
        "pension", "gratuity", "compassionate appointment", "seniority", "termination",
        "disciplinary enquiry", "suspension", "departmental proceedings", "cat order"
    ],
    "tax": [
        "income tax", "gst", "itat", "tax assessment", "c.i.t", "section 148", "input tax credit",
        "customs excise"
    ],
    "contempt": [
        "contempt of court", "cont.cas", "wilful disobedience", "non-compliance of court order"
    ],
    "constitutional": [
        "constitutional validity", "ultra vires", "article 14", "article 19", "article 21",
        "basic structure", "legislative competence"
    ],
}

# Mapping specific case types to broad legal domains
CASE_TYPE_TO_DOMAIN = {
    "bail": "Criminal Law (Bail & Personal Liberty)",
    "criminal_appeal": "Criminal Appellate Jurisdiction",
    "criminal_revision": "Criminal Revisional Jurisdiction",
    "criminal": "Criminal Law & Procedure",
    "writ_civil": "Constitutional & Administrative Law",
    "writ_criminal": "Constitutional Criminal Jurisdiction",
    "motor_accident": "Motor Accident Claims & Tort Law",
    "contract": "Commercial & Contract Law",
    "cheque_bounce": "Banking & Negotiable Instruments Law",
    "civil": "Civil Law & Procedure",
    "civil_appeal": "Civil Appellate Jurisdiction",
    "property": "Property & Real Estate Law",
    "family": "Family & Matrimonial Law",
    "arbitration": "Alternative Dispute Resolution (Arbitration)",
    "consumer": "Consumer Protection Law",
    "service": "Service & Labour Law",
    "tax": "Direct & Indirect Taxation Law",
    "contempt": "Contempt of Court Jurisdiction",
    "constitutional": "Constitutional Law",
    "other": "General Legal Jurisdiction",
}


# ── SECTION EXTRACTION REGEX ───────────────────────────────────────────
_SECTION_PATTERNS = [
    # Explicit Section/Sec/S.
    r"\b(?:sections?|secs?\.?|s\.?)\s*([0-9]{1,4}(?:-[a-z0-9]+)?|[0-9]{1,4}[a-z]?)\b",
    # Articles in Constitution
    r"\b(?:articles?|arts?\.?)\s*([0-9]{1,3}[a-z]?)\b",
    # Orders and Rules in CPC
    r"\border\s*([ivxldcm0-9]+)\s*(?:rule\s*([0-9]+))?\b",
    # Standalone 3 or 4 digit statutory code numbers (e.g. 438, 439, 482, 420, 302, 138, 166, 226)
    r"\b(438|439|482|302|304|307|323|325|376|379|380|384|406|409|420|467|468|471|498a|506|120b|138|139|166|140|226|227|32|136)\b",
]

# ── USER POSITION REGEX ─────────────────────────────────────────────────
_POSITION_CUES = {
    "petitioner": [
        r"\b(?:i am the petitioner|as the petitioner|petitioner seeks|filed by the petitioner|on behalf of petitioner|applicant\/petitioner)\b",
        r"\b(?:seeking (?:relief|quashing|mandamus|writ)|petition is filed)\b",
    ],
    "applicant": [
        r"\b(?:applicant seeks|as the applicant|i am the applicant|bail applicant|anticipatory bail application)\b",
        r"\b(?:pre-arrest (?:bail|protection)|protection from arrest|seeking anticipatory bail|seeking bail|facing (?:imminent )?arrest)\b",
    ],
    "appellant": [
        r"\b(?:i am the appellant|as the appellant|appellant appeals|appellant is aggrieved|appeal filed by)\b",
    ],
    "plaintiff": [
        r"\b(?:i am the plaintiff|as the plaintiff|plaintiff filed|suit instituted by|plaintiff claims)\b",
    ],
    "respondent": [
        r"\b(?:i am the respondent|as the respondent|respondent submits|opposing the petition|counsel for respondent)\b",
    ],
    "defendant": [
        r"\b(?:i am the defendant|as the defendant|defendant contends|written statement filed|defendant disputes)\b",
    ],
    "accused": [
        r"\b(?:i am the accused|accused is facing|allegations against me|falsely implicated|custodial interrogation|threatened with arrest)\b",
    ],
    "complainant": [
        r"\b(?:i am the complainant|informant|victim|lodged the fir|complainant filed)\b",
    ],
}


class CaseUnderstandingEngine:
    """
    Parses and structures arbitrary legal narratives into verified metadata profiles.
    """

    def extract_acts(self, text: str) -> List[str]:
        """Detect Indian Acts and statutory frameworks referenced in text."""
        detected = []
        text_lower = text.lower()
        for act_name, patterns in ACT_PATTERNS.items():
            for p in patterns:
                if re.search(p, text_lower, re.IGNORECASE):
                    detected.append(act_name)
                    break
        return detected

    def extract_sections(self, text: str) -> List[str]:
        """Extract exact Section, Article, and Order numbers from text."""
        sections = set()
        for pat in _SECTION_PATTERNS:
            matches = re.findall(pat, text, re.IGNORECASE)
            for m in matches:
                if isinstance(m, tuple):
                    for part in m:
                        if part and len(part.strip()) > 0:
                            sections.add(part.strip().upper())
                elif m and len(m.strip()) > 0:
                    sections.add(m.strip().upper())

        # Clean noise (skip years like 1988, 2023, 1872 or long text phrases)
        cleaned = []
        for s in sorted(list(sections)):
            s_clean = s.strip()
            # Skip 4-digit years
            if s_clean.isdigit() and (1800 <= int(s_clean) <= 2030 or len(s_clean) > 4):
                continue
            # Must be a reasonable section length and not a full act name
            if len(s_clean) > 12 or len(s_clean) == 0:
                continue
            # Skip common act words
            if s_clean.lower() in {"act", "code", "bns", "bnss", "ipc", "crpc", "cpc", "order", "rule", "section", "article"}:
                continue
            cleaned.append(s_clean)
        return cleaned

    def detect_user_position(self, text: str, explicit_position: Optional[str] = None) -> str:
        """Infer user's procedural position (petitioner, respondent, etc.)."""
        if explicit_position and explicit_position.strip():
            pos = explicit_position.strip().lower()
            if pos in ["petitioner", "applicant", "appellant", "plaintiff", "respondent", "defendant", "accused", "complainant"]:
                return pos

        text_lower = text.lower()
        for pos_label, patterns in _POSITION_CUES.items():
            for p in patterns:
                if re.search(p, text_lower, re.IGNORECASE):
                    return pos_label

        # Default heuristic based on common legal filings
        if "bail" in text_lower or "438" in text_lower or "439" in text_lower:
            return "applicant"
        if "writ" in text_lower or "article 226" in text_lower:
            return "petitioner"
        if "appeal" in text_lower:
            return "appellant"
        if "suit" in text_lower or "recovery" in text_lower:
            return "plaintiff"

        return "unknown"

    def classify_case_type(self, text: str, explicit_type: Optional[str] = None) -> Tuple[str, float]:
        """
        Classify the case category from text or normalize explicit user input.
        Returns (case_type, confidence_score).
        """
        if explicit_type and explicit_type.strip():
            raw = explicit_type.strip().lower()
            # Check direct mapping
            for cat, keywords in CATEGORY_KEYWORDS.items():
                if raw == cat or raw in keywords:
                    return cat, 0.95
                if cat in raw:
                    return cat, 0.90

        # Automated classification using keyword frequency & statutory weights
        text_lower = text.lower()
        scores: Dict[str, float] = {cat: 0.0 for cat in CATEGORY_KEYWORDS}

        for cat, keywords in CATEGORY_KEYWORDS.items():
            for kw in keywords:
                if kw in text_lower:
                    # Multi-word terms give higher confidence
                    weight = 2.5 if " " in kw else 1.0
                    scores[cat] += weight

        # Special statutory overrides
        if "section 438" in text_lower or "anticipatory bail" in text_lower or "section 439" in text_lower:
            scores["bail"] += 5.0
        if "section 138" in text_lower or "cheque bounce" in text_lower or "dishonour of cheque" in text_lower:
            scores["cheque_bounce"] += 5.0
        if "article 226" in text_lower or "writ petition" in text_lower:
            if "service" in text_lower or "pension" in text_lower:
                scores["writ_civil"] += 3.0
                scores["service"] += 2.0
            else:
                scores["writ_civil"] += 4.0
        if "section 166" in text_lower or "mact" in text_lower or "motor accident" in text_lower:
            scores["motor_accident"] += 5.0
        if "section 73" in text_lower and "contract" in text_lower:
            scores["contract"] += 5.0

        best_cat = max(scores, key=scores.get)
        max_score = scores[best_cat]

        if max_score == 0.0:
            return "other", 0.30

        confidence = min(0.98, 0.50 + (max_score * 0.08))
        return best_cat, round(confidence, 2)

    def extract_facts_and_issues(self, text: str) -> Tuple[List[str], List[str]]:
        """Extract key factual sentences and legal issues."""
        sentences = [s.strip() for s in re.split(r"[.\n]+", text) if len(s.strip()) > 15]

        facts = []
        issues = []

        issue_indicators = ["whether", "issue is", "contention", "seeking relief", "alleged that", "challenge", "ground"]

        for s in sentences:
            s_lower = s.lower()
            if any(ind in s_lower for ind in issue_indicators):
                issues.append(s)
            else:
                facts.append(s)

        if not issues and sentences:
            issues = [sentences[0]]

        return facts[:5], issues[:3]

    def extract_court_jurisdiction(self, text: str, explicit_court: Optional[str] = None) -> Optional[str]:
        """Identify target court or High Court."""
        if explicit_court and explicit_court.strip():
            return explicit_court.strip()

        court_keywords = [
            "Supreme Court", "Delhi High Court", "Bombay High Court", "Madras High Court",
            "Calcutta High Court", "Patna High Court", "Karnataka High Court", "Allahabad High Court",
            "Gujarat High Court", "Kerala High Court", "Punjab & Haryana High Court", "Rajasthan High Court",
            "Madhya Pradesh High Court", "Telangana High Court", "Andhra Pradesh High Court",
            "High Court", "Sessions Court", "District Court", "NCDRC", "CAT", "ITAT", "MACT"
        ]

        for c in court_keywords:
            if re.search(r"\b" + re.escape(c) + r"\b", text, re.IGNORECASE):
                return c

        return "High Court"

    def extract_procedural_remedy_and_tests(self, text: str, case_type: str) -> Tuple[Optional[str], List[str]]:
        """
        Extracts the precise procedural vehicle/remedy sought and applicable judicial tests.
        Prevents merely matching the same substantive penal sections (e.g. IPC 420)
        by aligning with the core procedural issue evaluated by the court.
        """
        text_lower = text.lower()
        remedy = None
        tests = []

        # 1. Procedural Remedies / Vehicles
        if "438" in text_lower or "anticipatory bail" in text_lower or "pre-arrest" in text_lower:
            remedy = "anticipatory_bail"
        elif "439" in text_lower or "regular bail" in text_lower or "bail application" in text_lower:
            remedy = "regular_bail"
        elif "482" in text_lower or "quash" in text_lower or "quashing" in text_lower:
            remedy = "quashing_482"
        elif "397" in text_lower or "401" in text_lower or "revision" in text_lower:
            remedy = "criminal_revision"
        elif "article 226" in text_lower or "article 32" in text_lower or "writ" in text_lower:
            remedy = "writ_petition"
        elif "order 39" in text_lower or "temporary injunction" in text_lower or "interim injunction" in text_lower:
            remedy = "temporary_injunction"
        elif "section 138" in text_lower or "cheque" in text_lower or "139" in text_lower:
            remedy = "cheque_dishonour_defense"
        elif "appeal" in text_lower:
            remedy = "appellate_review"
        else:
            remedy = case_type

        # 2. Judicial Tests & Grounds
        test_patterns = {
            "custodial_interrogation_necessity": ["custodial interrogation", "custody not required", "no recovery", "cooperated with investigation", "cooperation"],
            "clean_antecedents": ["clean antecedents", "no criminal antecedent", "no criminal history", "first offender", "first time"],
            "parity_relief": ["parity", "co-accused", "enlarged on bail", "granted bail"],
            "delay_in_trial_or_fir": ["delay in lodging", "delay in trial", "prolonged incarceration", "charge-sheet filed", "chargesheet submitted"],
            "civil_dispute_clothed_as_offense": ["civil in nature", "civil dispute", "breach of contract", "commercial transaction", "monetary dispute", "business transaction"],
            "procedural_non_compliance_41a": ["section 41a", "41a crpc", "arnesh kumar", "notice not served", "arrest guideline"],
            "statutory_presumption_rebuttal": ["security cheque", "rebutted presumption", "preponderance of probability", "statutory notice", "blank cheque"],
            "prima_facie_and_balance_of_convenience": ["prima facie", "balance of convenience", "irreparable injury", "irreparable loss", "triable issue"],
            "statutory_bar_or_maintainability": ["maintainability", "statutory bar", "alternative remedy", "locus standi", "res judicata"],
        }

        for test_name, keywords in test_patterns.items():
            if any(kw in text_lower for kw in keywords):
                tests.append(test_name)

        return remedy, tests

    def understand_case(
        self,
        description: str,
        case_type: Optional[str] = None,
        court: Optional[str] = None,
        acts: Optional[List[str]] = None,
        sections: Optional[List[str]] = None,
        user_position: Optional[str] = None,
    ) -> StructuredCaseProfile:
        """
        Main orchestration: converts raw case input into a complete StructuredCaseProfile.
        """
        # Extract statutory acts & sections
        detected_acts = sorted(list(set((acts or []) + self.extract_acts(description))))
        
        # Normalize and clean explicit user sections and extracted sections
        raw_sections = (sections or []) + self.extract_sections(description)
        cleaned_sections = []
        for s in raw_sections:
            extracted = self.extract_sections(s)
            if extracted:
                cleaned_sections.extend(extracted)
            else:
                s_clean = re.sub(r"^(?:section|sec|s|article|art)\.?\s*", "", s, flags=re.IGNORECASE).strip()
                if s_clean:
                    cleaned_sections.append(s_clean)
        detected_sections = sorted(list(set(cleaned_sections)))

        # Classify case category & confidence
        classified_type, confidence = self.classify_case_type(description, case_type)
        legal_domain = CASE_TYPE_TO_DOMAIN.get(classified_type, "General Legal Jurisdiction")

        # Extract Procedural Remedy & Core Judicial Tests
        remedy, tests = self.extract_procedural_remedy_and_tests(description, classified_type)

        # Detect User Position
        detected_position = self.detect_user_position(description, user_position)

        # Extract facts & issues
        facts, issues = self.extract_facts_and_issues(description)

        # Court jurisdiction
        extracted_court = self.extract_court_jurisdiction(description, court)

        return StructuredCaseProfile(
            case_type=classified_type,
            legal_domain=legal_domain,
            detected_acts=detected_acts,
            detected_sections=sorted(detected_sections),
            key_facts=facts,
            legal_issues=issues,
            user_position=detected_position,
            classification_confidence=confidence,
            extracted_court=extracted_court,
            procedural_remedy=remedy,
            judicial_tests=tests,
        )


# Singleton instance
_case_understanding_engine = None

def get_case_understanding_engine() -> CaseUnderstandingEngine:
    global _case_understanding_engine
    if _case_understanding_engine is None:
        _case_understanding_engine = CaseUnderstandingEngine()
    return _case_understanding_engine
