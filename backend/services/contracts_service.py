"""
Contract Analysis Service — Reads real file bytes and extracts risk clauses.
Supports PDF (pdfplumber), DOCX (python-docx), and plain TXT.
Falls back to keyword-based red-flag scanning when parsers are unavailable.
"""
import re
from typing import List, Tuple

from schemas.contracts import ContractAnalysisResponse, RedFlag


# ── Known high-risk contract clause patterns ─────────────────────────────────
RISK_PATTERNS: List[Tuple[str, str, str]] = [
    # (pattern, risk_level, explanation)
    (
        r"\bindemnif(?:y|ication|ies)\b.{0,120}unlimited\b",
        "high",
        "Unlimited indemnification clause detected. This exposes you to uncapped financial liability."
    ),
    (
        r"\b(?:liquidated damages|penalty clause)\b.{0,80}\b(?:50|60|70|80|90|100)\s*%",
        "high",
        "Extremely high liquidated damages percentage. Likely unenforceable under Section 74 of the Indian Contract Act."
    ),
    (
        r"\bautomatic\s+renewal\b.{0,120}(?:without\s+notice|unless\s+cancelled)",
        "medium",
        "Auto-renewal clause without prior notice may lock parties into unwanted extensions."
    ),
    (
        r"\bunilateral(?:ly)?\s+(?:amend|modify|change|alter)\b",
        "high",
        "One-sided amendment right allows counterparty to change terms without your consent."
    ),
    (
        r"\bwaive(?:r|s)?\s+(?:of\s+)?(?:right|claim|remedy)",
        "medium",
        "Broad waiver clause may strip you of statutory remedies available under Indian law."
    ),
    (
        r"\bnon[\-\s]compete\b.{0,120}\b(?:5|6|7|8|9|10)\s+years\b",
        "high",
        "Non-compete period exceeding 5 years may be void under Section 27 of the Indian Contract Act."
    ),
    (
        r"\bforce\s+majeure\b.{0,200}(?:does\s+not\s+include|excluding)\b",
        "medium",
        "Force majeure clause has narrow exclusions that may leave you exposed during unforeseen events."
    ),
    (
        r"\bexclusive\s+jurisdiction\b.{0,80}\b(?:foreign|international|arbitration abroad)\b",
        "medium",
        "Foreign jurisdiction clause may make dispute resolution prohibitively expensive for an Indian party."
    ),
    (
        r"\bno\s+(?:refund|return)\b",
        "medium",
        "Blanket no-refund clause may be challenged under the Consumer Protection Act, 2019."
    ),
    (
        r"\blast\s+notice\b.{0,80}conclusive\b",
        "medium",
        "Clause making last notice conclusive can prevent you from disputing errors."
    ),
    (
        r"\bgoverning\s+law\b.{0,80}(?:england|singapore|uae|us|usa|united\s+states)",
        "medium",
        "Foreign governing law clause. Indian courts may still have jurisdiction but enforcement costs increase."
    ),
    (
        r"\bindemnif(?:y|ication)\b.{0,200}third[\-\s]party",
        "medium",
        "Third-party indemnification clause. Ensure scope is clearly defined to avoid open-ended liability."
    ),
]


def _extract_text_from_bytes(filename: str, content_type: str, file_bytes: bytes) -> str:
    """Extract plain text from PDF, DOCX, or TXT file bytes."""
    name_lower = filename.lower()

    # ── Plain text ────────────────────────────────────────────────────────────
    if name_lower.endswith(".txt") or "text/plain" in content_type:
        return file_bytes.decode("utf-8", errors="ignore")

    # ── PDF via pdfplumber ────────────────────────────────────────────────────
    if name_lower.endswith(".pdf") or "pdf" in content_type:
        try:
            import io
            import pdfplumber
            text_parts = []
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        text_parts.append(t)
            return "\n".join(text_parts)
        except ImportError:
            pass  # pdfplumber not installed — fallback to raw bytes decode
        except Exception:
            pass

    # ── DOCX via python-docx ──────────────────────────────────────────────────
    if name_lower.endswith(".docx") or "wordprocessingml" in content_type:
        try:
            import io
            from docx import Document
            doc = Document(io.BytesIO(file_bytes))
            return "\n".join(para.text for para in doc.paragraphs if para.text.strip())
        except ImportError:
            pass
        except Exception:
            pass

    # ── Fallback: raw byte decode ─────────────────────────────────────────────
    return file_bytes.decode("utf-8", errors="ignore")


def analyze_contract(
    filename: str,
    content_type: str,
    file_bytes: bytes,
) -> ContractAnalysisResponse:
    """
    Read and analyze contract file bytes.
    Scans for known risk patterns and returns flagged clauses with explanations.
    """
    # 1. Extract text
    text = _extract_text_from_bytes(filename, content_type, file_bytes)
    if not text.strip():
        return ContractAnalysisResponse(
            red_flags=[RedFlag(
                clause_text="[File content could not be extracted]",
                risk_level="medium",
                explanation="The contract file appears to be empty or in an unsupported format. Try uploading as .txt or .docx.",
                page_ref=1,
            )],
            overall_risk_score="Unknown",
        )

    # 2. Scan for risk patterns
    red_flags: List[RedFlag] = []
    paragraphs = [p.strip() for p in re.split(r"\n{2,}|\r\n\r\n", text) if len(p.strip()) > 20]

    for pattern, risk_level, explanation in RISK_PATTERNS:
        for para_idx, para in enumerate(paragraphs):
            match = re.search(pattern, para, re.IGNORECASE | re.DOTALL)
            if match:
                clause_snippet = para[:200].strip() + ("..." if len(para) > 200 else "")
                page_estimate = max(1, para_idx // 3 + 1)
                red_flags.append(RedFlag(
                    clause_text=clause_snippet,
                    risk_level=risk_level,
                    explanation=explanation,
                    page_ref=page_estimate,
                ))
                break  # one flag per pattern type

        if len(red_flags) >= 10:
            break

    # 3. Overall risk score
    high_count = sum(1 for f in red_flags if f.risk_level == "high")
    medium_count = sum(1 for f in red_flags if f.risk_level == "medium")

    if high_count >= 3:
        overall = "Critical"
    elif high_count >= 1:
        overall = "High"
    elif medium_count >= 3:
        overall = "Medium"
    elif medium_count >= 1:
        overall = "Low-Medium"
    else:
        overall = "Low"

    # 4. If no flags found, confirm clean
    if not red_flags:
        red_flags.append(RedFlag(
            clause_text="No high-risk clauses detected in the scanned contract text.",
            risk_level="low",
            explanation="Standard contract language. Recommend independent legal review before signing.",
            page_ref=1,
        ))

    return ContractAnalysisResponse(
        red_flags=red_flags,
        overall_risk_score=overall,
    )
