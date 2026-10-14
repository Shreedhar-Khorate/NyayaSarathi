"""
Contract Analysis Service — Real AI analysis of contract text and risk clauses.
Supports PDF (pdfplumber), DOCX (python-docx), and plain TXT.
Dynamically extracts clauses, evaluates risk levels, and explains legal exposure under Indian law.
"""
import re
from typing import List, Tuple, Dict, Any

from schemas.contracts import ContractAnalysisResponse, RedFlag
from services.war_room_service import _call_llm_json, _ensure_list
from logger import get_logger

log = get_logger("nyayasarathi.contracts_service")


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
    Read and dynamically analyze contract file bytes using AI inference.
    Extracts high-risk clauses, assigns risk ratings, and cites Indian statutory exposure.
    """
    # 1. Extract text from uploaded bytes
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

    # 2. Dynamic AI Contract Risk Analysis
    system_prompt = (
        "You are an expert Indian Contract Law Legal Counsel.\n"
        "Analyze the provided contract text and identify high-risk, one-sided, ambiguous, or legally precarious clauses "
        "under Indian law (e.g. Indian Contract Act 1872, Specific Relief Act 1963, Arbitration & Conciliation Act 1996, "
        "Consumer Protection Act 2019, etc.).\n\n"
        "Return strictly a JSON object with this schema:\n"
        "{\n"
        '  "red_flags": [\n'
        "    {\n"
        '      "clause_text": "verbatim excerpt or concise snippet of clause from text (max 200 chars)",\n'
        '      "risk_level": "high" | "medium" | "low",\n'
        '      "explanation": "concise legal explanation citing relevant Indian law / statutory section (e.g. Section 27, Section 74 Contract Act, unilateral alteration, uncapped liability)",\n'
        '      "page_ref": 1\n'
        "    }\n"
        "  ],\n"
        '  "overall_risk_score": "Critical" | "High" | "Medium" | "Low-Medium" | "Low"\n'
        "}"
    )

    sample_text = text[:8000]
    user_prompt = (
        f"Contract Document: {filename}\n"
        f"Document Excerpt:\n{sample_text}\n\n"
        "Analyze the contract clauses and provide your structured legal risk assessment in JSON."
    )

    try:
        data, provider, model, _, _ = _call_llm_json(system_prompt, user_prompt)
        if isinstance(data, dict) and data.get("red_flags"):
            parsed_flags = []
            for rf in data["red_flags"]:
                if isinstance(rf, dict) and rf.get("clause_text") and rf.get("explanation"):
                    parsed_flags.append(
                        RedFlag(
                            clause_text=str(rf["clause_text"])[:300],
                            risk_level=str(rf.get("risk_level", "medium")).lower(),
                            explanation=str(rf["explanation"]),
                            page_ref=int(rf.get("page_ref", 1)) if str(rf.get("page_ref", "1")).isdigit() else 1,
                        )
                    )
            if parsed_flags:
                overall_score = str(data.get("overall_risk_score", "Medium"))
                return ContractAnalysisResponse(
                    red_flags=parsed_flags,
                    overall_risk_score=overall_score,
                )
    except Exception as e:
        log.warning(f"AI contract analysis failed, falling back to dynamic heuristic scan: {e}")

    # 3. Dynamic Heuristic Scan Fallback
    paragraphs = [p.strip() for p in re.split(r"\n{2,}|\r\n\r\n", text) if len(p.strip()) > 20]
    red_flags: List[RedFlag] = []

    heuristic_rules = [
        (r"\bindemnif(?:y|ication|ies)\b", "medium", "Indemnification obligation detected. Review scope of indemnity and ensure liability is capped.", 1),
        (r"\b(?:liquidated damages|penalty)\b", "high", "Liquidated damages/penalty provision. In Indian law under Section 74 Contract Act, only reasonable compensation is enforceable.", 1),
        (r"\bautomatic\s+renewal\b", "medium", "Automatic renewal clause detected. Ensure adequate prior notice requirement before lock-in.", 1),
        (r"\bunilateral(?:ly)?\s+(?:amend|modify|change|alter)\b", "high", "Unilateral modification clause permits the counterparty to alter contractual terms without prior written consent.", 1),
        (r"\bnon[\-\s]compete\b", "high", "Restrictive covenant / non-compete clause. Post-termination restraints of trade may be void under Section 27 of the Indian Contract Act.", 1),
        (r"\bexclusive\s+jurisdiction\b", "medium", "Jurisdiction clause specifying forum for legal disputes. Verify geographical convenience and dispute cost implications.", 1),
    ]

    for pattern, risk_level, explanation, page in heuristic_rules:
        for idx, para in enumerate(paragraphs):
            if re.search(pattern, para, re.IGNORECASE):
                clause_snippet = para[:200].strip() + ("..." if len(para) > 200 else "")
                red_flags.append(RedFlag(
                    clause_text=clause_snippet,
                    risk_level=risk_level,
                    explanation=explanation,
                    page_ref=max(1, idx // 3 + 1),
                ))
                break
        if len(red_flags) >= 8:
            break

    if not red_flags:
        red_flags.append(RedFlag(
            clause_text=paragraphs[0][:200] if paragraphs else "General contract text",
            risk_level="low",
            explanation="No conspicuous high-risk clauses identified in preliminary scan. Independent advocate review recommended.",
            page_ref=1,
        ))

    high_count = sum(1 for f in red_flags if f.risk_level == "high")
    overall = "High" if high_count >= 2 else "Medium" if high_count == 1 else "Low"

    return ContractAnalysisResponse(
        red_flags=red_flags,
        overall_risk_score=overall,
    )

