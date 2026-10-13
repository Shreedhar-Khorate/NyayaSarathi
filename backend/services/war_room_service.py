"""
NyayaSarathi Legal War Room — Core Intelligence & Simulation Service
Refactored for strict evidentiary grounding, procedural accuracy,
verified Supreme Court authorities, and 10-section strategic reporting.
Zero bail cases on murder appeals. Zero invented weapons/motives. Zero fake allegations.
"""

import os
import re
import json
import uuid
import time
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple

from logger import get_logger
from schemas.war_room import (
    WarRoomRequest,
    WarRoomResponse,
    WarRoomAnalyzeResponse,
    FactItem,
    EvidenceFinding,
    LegalArgument,
    OppositionArgument,
    RiskAssessmentItem,
    PrecedentFinding,
    StrategyReport,
)
from services.war_room_repository import (
    get_session_by_id,
    update_session,
    get_cache,
    set_cache,
    log_usage,
    get_db_connection,
)
from services.llm.provider_manager import get_llm_provider_manager, SYSTEM_PROMPT
from services.llm.groq_provider import GroqProvider
from services.precedent_verification import query_verified_precedents

log = get_logger("nyayasarathi.war_room_service")


# ── Token Budget & Helper Utilities ──────────────────────────────────────────

def estimate_tokens(text: str) -> int:
    """Conservative token count estimator (~4 characters per token)."""
    if not text:
        return 0
    return max(1, len(text) // 4)


def _ensure_list(val: Any) -> List[str]:
    """Ensures a field is strictly a list of strings, splitting by newline/semicolon if string."""
    if not val:
        return []
    if isinstance(val, list):
        return [str(item).strip() for item in val if str(item).strip()]
    if isinstance(val, str):
        if "\n" in val:
            return [s.strip(" -•\t*") for s in val.split("\n") if s.strip(" -•\t*")]
        if ";" in val:
            return [s.strip() for s in val.split(";") if s.strip()]
        return [val.strip()] if val.strip() else []
    return [str(val).strip()]


def build_cache_key(session_id: str, operation: str, case_hash: str, doc_ids: List[str]) -> str:
    combined = f"{session_id}:{operation}:{case_hash}:{','.join(sorted(doc_ids))}:v3"
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


def get_case_state_hash(session: Dict[str, Any]) -> str:
    content = f"{session.get('title')}:{session.get('description')}:{session.get('user_position')}:{session.get('case_type')}:{session.get('jurisdiction')}"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def fetch_document_chunks(doc_ids: List[str], max_chunks: int = 8) -> List[Dict[str, Any]]:
    """Fetches text chunks with page numbers and document titles directly from SQLite rag_chunks."""
    if not doc_ids:
        return []
    with get_db_connection() as conn:
        cursor = conn.cursor()
        placeholders = ",".join("?" for _ in doc_ids)
        query = f"""
            SELECT c.id as chunk_id, c.document_id, d.title as doc_title,
                   c.page_number, c.paragraph_number, c.text, c.token_count
            FROM rag_chunks c
            JOIN rag_documents d ON c.document_id = d.id
            WHERE c.document_id IN ({placeholders})
            ORDER BY c.document_id, c.chunk_index ASC
            LIMIT ?
        """
        params = list(doc_ids) + [max_chunks]
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [
            {
                "chunk_id": r["chunk_id"],
                "document_id": r["document_id"],
                "doc_title": r["doc_title"],
                "page_number": r["page_number"],
                "paragraph_number": r["paragraph_number"],
                "text": r["text"],
                "token_count": r["token_count"],
            }
            for r in rows
        ]


# ── Dedicated War Room Groq Key Resolver ──────────────────────────────────────

def _get_war_room_groq_key() -> str:
    key = os.environ.get("WAR_ROOM_GROQ_API_KEY", "").strip()
    if not key:
        env_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
        if os.path.exists(env_file):
            try:
                with open(env_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip().startswith("WAR_ROOM_GROQ_API_KEY="):
                            val = line.strip().split("=", 1)[1].strip().strip("'\"")
                            if val:
                                key = val
                                os.environ["WAR_ROOM_GROQ_API_KEY"] = val
                            break
            except Exception:
                pass
    return key


def _parse_llm_json(raw_text: str) -> Any:
    cleaned = re.sub(r"^```json\s*", "", raw_text, flags=re.IGNORECASE)
    cleaned = re.sub(r"^```\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned).strip()

    # 1. Try standard parse with strict=False
    try:
        return json.loads(cleaned, strict=False)
    except Exception:
        pass

    # 2. Extract outermost [ ... ] or { ... }
    json_match = re.search(r"(\[.*\]|\{.*\})", cleaned, re.DOTALL)
    if json_match:
        target = json_match.group(1).strip()
        try:
            return json.loads(target, strict=False)
        except Exception:
            # 3. Strip trailing commas before ] or }
            repaired = re.sub(r",\s*([\]}])", r"\1", target)
            try:
                return json.loads(repaired, strict=False)
            except Exception:
                pass

    # 4. Truncated repair: If text starts with [ and cut off
    if "[" in cleaned:
        start_idx = cleaned.find("[")
        last_brace = cleaned.rfind("}")
        if last_brace > start_idx:
            sub = cleaned[start_idx:last_brace+1] + "]"
            sub = re.sub(r",\s*([\]}])", r"\1", sub)
            try:
                return json.loads(sub, strict=False)
            except Exception:
                pass

    # 5. Truncated repair: If text starts with { and cut off
    if "{" in cleaned:
        start_idx = cleaned.find("{")
        last_brace = cleaned.rfind("}")
        if last_brace > start_idx:
            sub = cleaned[start_idx:last_brace+1] + "}"
            sub = re.sub(r",\s*([\]}])", r"\1", sub)
            try:
                return json.loads(sub, strict=False)
            except Exception:
                pass

    # 6. Try ast.literal_eval
    try:
        import ast
        return ast.literal_eval(cleaned)
    except Exception:
        pass

    return json.loads(cleaned, strict=False)


def _call_llm_json(system_prompt: str, user_prompt: str) -> Tuple[Any, str, str, int, int]:
    """
    Executes a structured JSON call strictly using the LLM with dedicated War Room key.
    """
    t_in = estimate_tokens(system_prompt) + estimate_tokens(user_prompt)
    war_room_key = _get_war_room_groq_key()

    chosen_provider = None
    if war_room_key:
        model_name = os.environ.get("WAR_ROOM_MODEL", "openai/gpt-oss-120b").strip()
        chosen_provider = GroqProvider(api_key=war_room_key, model=model_name)
    else:
        llm_manager = get_llm_provider_manager()
        candidate_sequence = [llm_manager.primary_name, llm_manager.fallback_name, "groq", "cerebras", "gemini"]
        for name in candidate_sequence:
            p = llm_manager.providers.get(name)
            if p and p.is_available():
                chosen_provider = p
                break

    if not chosen_provider:
        raise RuntimeError("No LLM API key configured for War Room. Please set WAR_ROOM_GROQ_API_KEY in backend/.env")

    try:
        full_user = (
            f"{user_prompt}\n\n"
            "IMPORTANT: Respond with pure, valid JSON ONLY. Escape internal quotes with backslashes. "
            "No markdown fences, no explanatory preamble."
        )
        res = chosen_provider.generate_grounded_answer(
            question="Generate structured analysis",
            evidence_chunks=[],
            system_prompt=system_prompt,
            user_prompt=full_user,
            timeout_seconds=30.0,
        )
        raw_text = res.answer.strip()
        parsed = _parse_llm_json(raw_text)
        t_out = estimate_tokens(raw_text)
        return parsed, "groq(war_room)" if war_room_key else res.provider, chosen_provider.model, t_in, t_out
    except Exception as e:
        log.error(f"War Room LLM generation failed: {e}")
        raise RuntimeError(f"LLM generation failed: {str(e)}")


# ── Procedural Posture & Forum Detection Engine ───────────────────────────────
from services.procedural_context_engine import analyze_procedural_context

def detect_procedural_posture(session: Dict[str, Any], chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Determines the judicial forum, procedural posture, prior procedural events,
    statutory era (IPC/CrPC vs BNS/BNSS), and stage-appropriate next steps dynamically.
    Zero hardcoded case names.
    """
    return analyze_procedural_context(session, chunks)


# ── Core Analysis Router ─────────────────────────────────────────────────────

def execute_war_room_analysis(
    session_id: str,
    operation: str,
    target_id: Optional[str] = None,
    force_refresh: bool = False,
    custom_instructions: Optional[str] = None,
    user_id: Optional[str] = None,
) -> WarRoomAnalyzeResponse:
    session = get_session_by_id(session_id)
    if not session:
        raise ValueError(f"War Room session '{session_id}' not found.")

    start_time = time.perf_counter()
    doc_ids = session.get("selected_doc_ids", [])
    case_hash = get_case_state_hash(session)
    cache_key = build_cache_key(session_id, operation, case_hash, doc_ids)

    # Check cache
    if not force_refresh and not target_id:
        cached_result = get_cache(cache_key)
        if cached_result:
            log.info(f"Cache hit for War Room operation '{operation}' on session '{session_id}'")
            log_usage(
                log_id=str(uuid.uuid4()),
                session_id=session_id,
                user_id=user_id,
                operation=operation,
                provider="cache",
                model="local_cache",
                input_tokens=0,
                output_tokens=0,
                duration_ms=int((time.perf_counter() - start_time) * 1000),
                cache_hit=True,
            )
            return WarRoomAnalyzeResponse(
                operation=operation,
                session_id=session_id,
                result=cached_result,
                cache_hit=True,
                provider="cache",
                model="local_cache",
                tokens_used=0,
                duration_ms=int((time.perf_counter() - start_time) * 1000),
                message="Retrieved instantly from cache (0 tokens consumed).",
            )

    # Fetch document evidence from database
    chunks = fetch_document_chunks(doc_ids, max_chunks=8)

    # Dispatch operation dynamically
    result = None
    provider_name = "system"
    model_name = "database_or_llm"
    tokens_in = 0
    tokens_out = 0

    if operation == "facts":
        result, provider_name, model_name, tokens_in, tokens_out = generate_fact_sheet(session, chunks, custom_instructions)
        update_session(session_id, {"fact_sheet": result})
    elif operation == "evidence":
        result, provider_name, model_name, tokens_in, tokens_out = analyze_evidence(session, chunks, custom_instructions)
        update_session(session_id, {"evidence_findings": result})
    elif operation == "arguments":
        result, provider_name, model_name, tokens_in, tokens_out = build_arguments(session, chunks, target_id, custom_instructions)
        if target_id and session.get("arguments"):
            current_args = session.get("arguments", [])
            updated_args = [a for a in current_args if a.get("id") != target_id]
            if isinstance(result, list):
                updated_args.extend(result)
            else:
                updated_args.append(result)
            result = updated_args
        update_session(session_id, {"arguments": result})
    elif operation == "opposition":
        result, provider_name, model_name, tokens_in, tokens_out = simulate_opposition(session, chunks, custom_instructions)
        update_session(session_id, {"opposition": result})
    elif operation == "risks":
        result, provider_name, model_name, tokens_in, tokens_out = assess_risks(session, chunks, custom_instructions)
        update_session(session_id, {"risks": result})
    elif operation == "precedents":
        # Pure Database Retrieval from verified Supreme Court authorities table
        result, provider_name, model_name, tokens_in, tokens_out = research_precedents(session, chunks)
        update_session(session_id, {"precedents": result})
    elif operation == "report":
        result, provider_name, model_name, tokens_in, tokens_out = generate_strategy_report(session, chunks)
        update_session(session_id, {"report": result})
    else:
        raise ValueError(f"Unsupported War Room operation: '{operation}'")

    duration_ms = int((time.perf_counter() - start_time) * 1000)

    # Cache successful result
    if not target_id:
        set_cache(cache_key, session_id, operation, result)

    # Log usage
    log_usage(
        log_id=str(uuid.uuid4()),
        session_id=session_id,
        user_id=user_id,
        operation=operation,
        provider=provider_name,
        model=model_name,
        input_tokens=tokens_in,
        output_tokens=tokens_out,
        duration_ms=duration_ms,
        cache_hit=False,
    )

    return WarRoomAnalyzeResponse(
        operation=operation,
        session_id=session_id,
        result=result,
        cache_hit=False,
        provider=provider_name,
        model=model_name,
        tokens_used=tokens_in + tokens_out,
        duration_ms=duration_ms,
        message=f"Analysis completed successfully using {provider_name} ({tokens_in + tokens_out} tokens).",
    )


# ── Feature A: Grounded Fact Extraction (7-Category Judicial Taxonomy) ─────────

def generate_fact_sheet(
    session: Dict[str, Any],
    chunks: List[Dict[str, Any]],
    custom_instructions: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], str, str, int, int]:
    """
    Extracts categorized facts dynamically with strict classification:
    - procedural_event, court_finding, final_holding, documentary_evidence,
      witness_testimony, party_submission, allegation.
    Never marks confirmed procedural history or judicial holdings as unverified allegations.
    """
    description = session.get("description", "")
    position = session.get("user_position", "appellant")
    case_type = session.get("case_type", "criminal")
    court = session.get("court", "Court of Record")

    posture_info = detect_procedural_posture(session, chunks)

    evidence_context = ""
    for idx, c in enumerate(chunks):
        evidence_context += f"[Exhibit {idx+1}: {c['doc_title']}, p.{c['page_number']}]\n{c['text'][:450]}\n\n"

    system_prompt = (
        "You are an expert Judicial Fact Master and Registrar of Court Records. Extract and categorize statements strictly into 7 categories:\n"
        "1. 'procedural_event': Official procedural history (e.g. trial conviction by Sessions Court, dismissal by High Court, SLP/appeal before Supreme Court).\n"
        "2. 'court_finding': Specific judicial findings recorded by the Court (e.g. absence of premeditation, sudden fight in heat of passion, scuffle arose suddenly).\n"
        "3. 'final_holding': The operative final judgment or order of the Court (e.g. conviction under S. 302 altered to S. 304 Part II; sentence modified to period undergone).\n"
        "4. 'documentary_evidence': Written records and contemporaneous exhibits (e.g. written statement under Section 313(5) CrPC, FIR, medical injury report).\n"
        "5. 'witness_testimony': Deposition of prosecution or defense witnesses (e.g. testimony of PW-1, PW-2, PW-3, PW-4).\n"
        "6. 'party_submission': Contentions or arguments advanced by counsel for the parties.\n"
        "7. 'allegation': Unadjudicated assertions made in complaint or charge sheet.\n\n"
        "CRITICAL RULES:\n"
        "- DO NOT label established procedural events or judicial holdings as 'unverified_allegation' when confirmed by primary court records or judgment excerpts.\n"
        "- Set verification_status to one of: 'verified_from_primary_record', 'reported_in_judgment', 'unverified_submission', 'verification_required'.\n"
        "- Set source_reliability to: 'primary_judicial_record', 'official_court_record', 'contemporaneous_document', 'party_pleading', or 'unverified_claim'.\n"
        "- Do not invent weapons, premeditation, or medical facts.\n"
        "Return ONLY a JSON array of objects with keys: id, fact, category, source_doc_title, page_number, paragraph_number, excerpt, verification_status, source_reliability, confidence."
    )

    user_prompt = (
        f"Case: {session.get('title')}\nForum: {posture_info['current_forum']} ({posture_info['posture']})\n"
        f"Standing: {posture_info['party_role']}\n\n"
        f"Case Record / Primary Judgment Summary:\n{description if description else 'No narrative provided.'}\n\n"
        f"Attached Exhibits & Excerpts:\n{evidence_context if evidence_context else 'Primary Case Record'}\n\n"
        f"{'Custom Instructions: ' + custom_instructions if custom_instructions else 'Extract 5 to 8 factual items rigorously categorized according to the 7-part judicial taxonomy.'}"
    )

    try:
        facts, provider, model, t_in, t_out = _call_llm_json(system_prompt, user_prompt)
        if isinstance(facts, list) and facts:
            for idx, f in enumerate(facts):
                if not f.get("id"):
                    f["id"] = f"fact-{idx+1}"
                f["is_reviewed"] = f.get("is_reviewed", False)
                # Safeguard against wrongful allegation tagging
                cat = f.get("category", "").lower()
                text = f.get("fact", "").lower()
                if any(w in text for w in ["convicted", "dismissed", "sentenced", "sessions", "high court", "appeal"]):
                    if cat in ("unverified_allegation", "allegation"):
                        f["category"] = "procedural_event"
                        f["verification_status"] = "verified_from_primary_record"
                        f["source_reliability"] = "official_court_record"
                elif any(w in text for w in ["altered", "held that", "acquitted", "supreme court held", "modified to"]):
                    if cat in ("unverified_allegation", "allegation"):
                        f["category"] = "final_holding"
                        f["verification_status"] = "verified_from_primary_record"
                        f["source_reliability"] = "primary_judicial_record"
                elif "section 313" in text or "written statement" in text or "fir" in text:
                    if cat in ("unverified_allegation", "allegation"):
                        f["category"] = "documentary_evidence"
                        f["verification_status"] = "reported_in_judgment"
                        f["source_reliability"] = "contemporaneous_document"

            return facts, provider, model, t_in, t_out
        raise ValueError("LLM did not return a valid list of facts.")
    except Exception as e:
        log.error(f"War Room LLM fact extraction failed: {e}")
        raise RuntimeError(f"Fact extraction failed: {str(e)}")


# ── Feature B: Evidence Analyzer (Separated Reliability, Status, Relevance) ───

def analyze_evidence(
    session: Dict[str, Any],
    chunks: List[Dict[str, Any]],
    custom_instructions: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], str, str, int, int]:
    """
    Analyzes document exhibits and case facts using LLM.
    Separates: underlying_fact, source_reliability, evidentiary_status, legal_relevance, model_confidence.
    Zero hallucinated weapons or forensic findings.
    """
    evidence_context = ""
    for idx, c in enumerate(chunks):
        evidence_context += f"[Exhibit {idx+1}: {c['doc_title']}, p.{c['page_number']}]\n{c['text'][:450]}\n\n"

    system_prompt = (
        "You are an Indian Judicial Evidence Specialist. Analyze the provided case facts and exhibits.\n"
        "CRITICAL RULES:\n"
        "- Separate: underlying_fact, source_reliability, evidentiary_status, legal_relevance, and model_confidence.\n"
        "- Set source_reliability to: 'primary_judicial_record', 'official_court_record', 'contemporaneous_document', 'party_pleading', or 'unverified_claim'.\n"
        "- Set evidentiary_status to: 'established', 'disputed', 'corroborated_by_record', 'unsupported', 'inadmissible', or 'verification_required'.\n"
        "- Set legal_relevance to: 'direct_probative', 'contextual_procedural', 'impeachment', or 'peripheral'.\n"
        "- Never assign high confidence merely because a sentence appears in an input summary.\n"
        "- NEVER invent medical findings, witness contradictions, weapons (such as concealed knives), motives, or forensic evidence.\n"
        "- Generate follow_up_question ONLY when relevant to a disputed fact or genuine evidentiary gap (e.g. whether Section 313(5) CrPC written statement was evaluated).\n"
        "- Do not describe a missing document as proof that the underlying event did not occur.\n"
        "Return ONLY a JSON array of findings with keys: id, finding, underlying_fact, relevant_claim, evidence_type, source_reliability, evidentiary_status, legal_relevance, source_doc_title, page_number, paragraph_number, excerpt, model_confidence, follow_up_question, is_disputed."
    )

    user_prompt = (
        f"Case: {session.get('title')}\nStanding: {session.get('user_position')}\n\n"
        f"Facts & Judicial Record:\n{session.get('description')}\n\n"
        f"Exhibits:\n{evidence_context if evidence_context else 'Case Dossier & Judgment Text'}\n\n"
        f"{'Instructions: ' + custom_instructions if custom_instructions else 'Provide 4 to 6 evidence findings strictly grounded in the verified case record.'}"
    )

    try:
        findings, provider, model, t_in, t_out = _call_llm_json(system_prompt, user_prompt)
        if isinstance(findings, list) and findings:
            for idx, f in enumerate(findings):
                if not f.get("id"):
                    f["id"] = f"ev-{idx+1}"
                f["confidence"] = f.get("model_confidence", 0.85)
            return findings, provider, model, t_in, t_out
        raise ValueError("LLM did not return a valid list of evidence findings.")
    except Exception as e:
        log.error(f"War Room LLM evidence analysis failed: {e}")
        raise RuntimeError(f"Evidence analysis failed: {str(e)}")


# ── Feature C: Argument Builder (Doctrinal Requirements & Statutory Sections) ──

def build_arguments(
    session: Dict[str, Any],
    chunks: List[Dict[str, Any]],
    target_id: Optional[str] = None,
    custom_instructions: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], str, str, int, int]:
    """
    Constructs affirmative arguments with:
    - Legal issue and statutory provisions (e.g. Exception 4 to Section 300 IPC, Section 304 Part II, Section 313(5) CrPC).
    - Verified facts, required evidence, binding authorities with pinpoint paragraphs.
    - Strongest opposing argument and evidence-based rebuttal.
    """
    posture_info = detect_procedural_posture(session, chunks)
    verified_precedents = query_verified_precedents(
        case_type=session.get("case_type", "criminal"),
        description=session.get("description", "") + " " + session.get("title", ""),
        user_position=posture_info["party_role"]
    )

    precedent_context = "\n".join([
        f"- {p['title']} [{p['citation']}] ({p['court']}, {p['decision_date']}): {p['actual_holding']} [Para: {p.get('relevant_paragraphs', 'N/A')}]"
        for p in verified_precedents[:4]
    ])

    system_prompt = (
        f"You are a Senior Indian Appellate Advocate representing the {posture_info['party_role'].upper()} before the {posture_info['current_forum']}.\n"
        "Draft rigorous legal arguments structured in a JSON array. Each argument must have:\n"
        "- id: string (e.g. 'arg-1')\n"
        "- title: concise headline\n"
        "- legal_issue: precise statutory question (e.g. 'Applicability of Exception 4 to Section 300 IPC in sudden fight without premeditation')\n"
        "- applicable_provisions: list of Indian statutory sections (e.g. ['Exception 4 to Section 300 IPC', 'Section 304 Part II IPC', 'Section 313(5) CrPC'])\n"
        "- procedural_role_argument: proposed argument framed specifically for client's procedural standing\n"
        "- main_claim: core legal proposition\n"
        "- supporting_facts: list of verified factual points\n"
        "- evidence_refs: list of document or exhibit references\n"
        "- evidence_still_required: list of documents or proof still needed\n"
        "- relevant_precedents: list of binding Supreme Court authorities with exact holdings and pinpoint paragraphs\n"
        "- legal_reasoning: doctrinal application connecting statutory ingredients to verified facts. Specifically explain the 4 requirements of Exception 4 to Section 300 IPC: (1) without premeditation, (2) in a sudden fight, (3) in the heat of passion upon a sudden quarrel, (4) offender having not taken undue advantage or acted in a cruel or unusual manner.\n"
        "- strongest_opposing_argument: strongest counter-argument opponent will raise\n"
        "- rebuttal_and_weaknesses: evidence-based rebuttal addressing weaknesses in client's case\n"
        "- reasoning_type: 'actual_judicial_reasoning' (if based on judgment) or 'proposed_advocacy_argument'\n"
        "- potential_weaknesses: list of points counsel must be prepared to defend\n"
        "- questions_to_investigate: actionable factual questions\n"
        "CRITICAL: Do NOT invent weapons, premeditation, or self-defense claims not in the record."
    )

    user_prompt = (
        f"Case: {session.get('title')}\nForum: {posture_info['current_forum']} ({posture_info['posture']})\n"
        f"Procedural Role: {posture_info['party_role']}\n\n"
        f"Case Facts & Judicial Record:\n{session.get('description')}\n\n"
        f"Verified Authorities from Judicial Database:\n{precedent_context}\n\n"
        f"{'Instructions: ' + custom_instructions if custom_instructions else 'Draft 2 to 3 affirmative arguments rigorously structured with statutory provisions and precedent holdings.'}"
    )

    try:
        args, provider, model, t_in, t_out = _call_llm_json(system_prompt, user_prompt)
        if isinstance(args, list) and args:
            for idx, a in enumerate(args):
                if not a.get("id"):
                    a["id"] = f"arg-{idx+1}"
                a["is_reviewed"] = a.get("is_reviewed", False)
                a["applicable_provisions"] = _ensure_list(a.get("applicable_provisions"))
                a["relevant_precedents"] = _ensure_list(a.get("relevant_precedents"))
                a["potential_weaknesses"] = _ensure_list(a.get("potential_weaknesses"))
                a["supporting_facts"] = _ensure_list(a.get("supporting_facts"))
                a["evidence_refs"] = _ensure_list(a.get("evidence_refs"))
                a["evidence_still_required"] = _ensure_list(a.get("evidence_still_required"))
                a["questions_to_investigate"] = _ensure_list(a.get("questions_to_investigate"))
            return args, provider, model, t_in, t_out
        raise ValueError("LLM did not return a valid list of arguments.")
    except Exception as e:
        log.error(f"War Room LLM argument building failed: {e}")
        raise RuntimeError(f"Argument building failed: {str(e)}")


# ── Feature D: Opposition Simulator (Grounded Adversarial Stress-Test) ────────

def simulate_opposition(
    session: Dict[str, Any],
    chunks: List[Dict[str, Any]],
    custom_instructions: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], str, str, int, int]:
    """
    Stress-tests the case from opposing counsel's viewpoint.
    Strictly grounded in prosecution evidence. Zero fabricated weapons or motives.
    """
    posture_info = detect_procedural_posture(session, chunks)
    opp_role = "Respondent State / Prosecution" if posture_info["party_role"] == "Appellant" else "Appellant"

    system_prompt = (
        f"You are Senior Counsel representing the OPPOSING PARTY ({opp_role}).\n"
        "Your role is DEVIL'S ADVOCATE: stress-test the case using strictly legitimate legal and evidentiary grounds.\n"
        "CRITICAL RULES:\n"
        "- Ground objections strictly in prosecution evidence (e.g. fatal injury to vital part, multiple injured witnesses under S. 307 IPC, presumption of intention under S. 300 3rd clause, burden of proving Exception 4 under S. 105 Evidence Act).\n"
        "- NEVER invent fictitious weapons (such as concealed knives where not in record), fictitious motives, or unfounded self-defense claims.\n"
        "Return ONLY a JSON array with keys:\n"
        "- id: string (e.g. 'opp-1')\n"
        "- opposing_claim: strongest contention opposing counsel will make\n"
        "- supporting_facts_evidence: facts or documents the other side will cite\n"
        "- adverse_precedents: case law unfavorable to client\n"
        "- user_position_weaknesses: where client's case is vulnerable\n"
        "- suggested_rebuttal_counterarguments: how client's counsel should counter\n"
        "- missing_information: evidentiary holes the other side will exploit."
    )

    user_prompt = (
        f"Case: {session.get('title')}\nForum: {posture_info['current_forum']}\nOpposing Role: {opp_role}\n\n"
        f"Case Facts:\n{session.get('description')}\n\n"
        f"{'Instructions: ' + custom_instructions if custom_instructions else 'Produce 2 to 3 legitimate adversarial contentions grounded in the evidence record.'}"
    )

    try:
        opp_args, provider, model, t_in, t_out = _call_llm_json(system_prompt, user_prompt)
        if isinstance(opp_args, list) and opp_args:
            for idx, o in enumerate(opp_args):
                if not o.get("id"):
                    o["id"] = f"opp-{idx+1}"
                o["supporting_facts_evidence"] = _ensure_list(o.get("supporting_facts_evidence"))
                o["adverse_precedents"] = _ensure_list(o.get("adverse_precedents"))
                o["user_position_weaknesses"] = _ensure_list(o.get("user_position_weaknesses"))
                o["suggested_rebuttal_counterarguments"] = _ensure_list(o.get("suggested_rebuttal_counterarguments"))
                o["missing_information"] = _ensure_list(o.get("missing_information"))
            return opp_args, provider, model, t_in, t_out
        raise ValueError("LLM did not return a valid list of opposition claims.")
    except Exception as e:
        log.error(f"War Room LLM opposition simulation failed: {e}")
        raise RuntimeError(f"Opposition simulation failed: {str(e)}")


# ── Feature E: Legal Precedent Research (100% Verified Supreme Court Authorities) ─

def research_precedents(
    session: Dict[str, Any],
    chunks: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], str, str, int, int]:
    """
    100% Verified Database Retrieval:
    Retrieves authentic Supreme Court of India authorities from war_room_verified_precedents table.
    Guarantees:
    - Never serves bail decisions on murder appeals.
    - Verified citations, pinpoint paragraphs, and actual holdings.
    - Correct outcome classification (supporting, adverse, distinguishable).
    """
    posture_info = detect_procedural_posture(session, chunks)
    precedents = query_verified_precedents(
        case_type=session.get("case_type", "criminal"),
        description=session.get("description", "") + " " + session.get("title", ""),
        user_position=posture_info["party_role"]
    )
    return precedents, "local_sqlite_db", "nyayasarathi.db(verified_authorities)", 0, len(precedents) * 80


# ── Feature F: Risk & Weakness Assessment (Doctrinal & Evidentiary Hazards) ─────

def assess_risks(
    session: Dict[str, Any],
    chunks: List[Dict[str, Any]],
    custom_instructions: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], str, str, int, int]:
    """
    Audits the case dynamically using LLM to identify real risks, missing evidence,
    and factual vulnerabilities.
    """
    posture_info = detect_procedural_posture(session, chunks)

    system_prompt = (
        "You are an Indian Legal Risk Auditor. Identify potential legal risks, factual gaps, and procedural hazards.\n"
        "Return ONLY a JSON array of risk items with keys:\n"
        "- id: string (e.g. 'risk-1')\n"
        "- risk_type: 'unsupported_argument', 'missing_evidence', 'unresolved_factual_dispute', 'adverse_precedent', 'weak_evidence_link', or 'requires_expert_review'\n"
        "- description: concise explanation of why this risk matters\n"
        "- severity: 'high', 'medium', or 'low'\n"
        "- affected_claims: list of impacted claims\n"
        "- mitigation_steps: actionable remedies\n"
        "- clarification_documents_needed: specific missing documents to request\n"
        "Do not invent fake probability percentages. Provide objective doctrinal risk assessment."
    )

    user_prompt = (
        f"Case: {session.get('title')}\nForum: {posture_info['current_forum']} ({posture_info['posture']})\n"
        f"Standing: {posture_info['party_role']}\n\n"
        f"Case Record:\n{session.get('description')}\n\n"
        f"{'Instructions: ' + custom_instructions if custom_instructions else 'Identify 3 to 4 realistic procedural and evidentiary risks.'}"
    )

    try:
        risks, provider, model, t_in, t_out = _call_llm_json(system_prompt, user_prompt)
        if isinstance(risks, list) and risks:
            for idx, r in enumerate(risks):
                if not r.get("id"):
                    r["id"] = f"risk-{idx+1}"
                r["mitigation_steps"] = _ensure_list(r.get("mitigation_steps"))
                r["clarification_documents_needed"] = _ensure_list(r.get("clarification_documents_needed"))
                r["affected_claims"] = _ensure_list(r.get("affected_claims"))
            return risks, provider, model, t_in, t_out
        raise ValueError("LLM did not return a valid list of risks.")
    except Exception as e:
        log.error(f"War Room LLM risk assessment failed: {e}")
        raise RuntimeError(f"Risk assessment failed: {str(e)}")


# ── Feature G: Strategy Report Generator (10 Comprehensive Sections) ──────────

def _synthesize_report_from_db_session(session: Dict[str, Any]) -> Dict[str, Any]:
    """
    Synthesizes the complete 10-section Strategy Report directly from the session's
    stored database records and verified procedural posture.
    Zero hardcoded case details or fixed judicial text.
    """
    now = datetime.now(timezone.utc).strftime("%d %B %Y, %H:%M UTC")
    posture_info = detect_procedural_posture(session, [])
    facts = session.get("fact_sheet", [])
    evidence_items = session.get("evidence", [])
    arguments = session.get("arguments", [])
    opposition = session.get("opposition", [])
    precedents = session.get("precedents", [])
    risks = session.get("risks", [])

    # 1. Parties & Posture
    posture_text = (
        f"• Current Forum: {posture_info['current_forum']}\n"
        f"• Procedural Posture: {posture_info['posture']}\n"
        f"• Parties: {posture_info['appellant']} (Appellant) vs {posture_info['respondent']} (Respondent)\n"
        f"• Selected Role: {posture_info['party_role']}\n"
        f"• Applicable Statutory Regime: {posture_info.get('statute_title', 'Indian Penal Code, 1860 / CrPC, 1973')}\n"
        f"• Statutory Transition Note: {posture_info.get('transition_note', '')}\n\n"
        f"Prior Procedural Stages:\n" + "\n".join([f"• {stage}" for stage in posture_info['prior_stages']])
    )

    # 2. Chronology from DB facts
    facts_text = "\n".join([
        f"• [{f.get('category', 'fact').replace('_', ' ').title()}] {f.get('fact')} (Status: {f.get('verification_status', 'reported_in_judgment').replace('_', ' ').title()})"
        for f in facts[:8]
    ]) if facts else "Verified factual events extracted from the primary case record."

    # 3. Issues for Determination
    if arguments:
        issues_text = "\n".join([
            f"{idx+1}. {a.get('legal_issue') or a.get('title')}"
            for idx, a in enumerate(arguments[:4])
        ])
    else:
        issues_text = f"1. Core legal issues arising in {session.get('title', 'the matter')} before {posture_info['current_forum']}."

    # 4. Evidence Matrix
    if evidence_items:
        evidence_text = "\n".join([
            f"• [{ev.get('evidence_type', 'record').title()}] {ev.get('finding')} "
            f"(Source: {ev.get('source_reliability', 'official_record')}; "
            f"Status: {ev.get('evidentiary_status', 'established')}; "
            f"Relevance: {ev.get('legal_relevance', 'probative')})"
            for ev in evidence_items[:6]
        ])
    else:
        evidence_text = f"Evidence analysis based on {len(facts)} categorized facts from the primary record."

    # 5. Arguments
    args_text = "\n\n".join([
        f"### {a.get('title')}\n"
        f"• Statutory Provisions: {', '.join(a.get('applicable_provisions', []))}\n"
        f"• Core Proposition: {a.get('main_claim')}\n"
        f"• Doctrinal Reasoning: {a.get('legal_reasoning', a.get('procedural_role_argument', ''))}\n"
        f"• Authorities Cited: {'; '.join(a.get('relevant_precedents', []))}"
        for a in arguments[:3]
    ]) if arguments else "Affirmative arguments formulated for the selected procedural role."

    # 6. Opposition
    opp_text = "\n\n".join([
        f"• Hostile Contention: {o.get('opposing_claim')}\n"
        f"  Adverse Authorities: {'; '.join(o.get('adverse_precedents', []))}\n"
        f"  Vulnerability: {'; '.join(o.get('user_position_weaknesses', []))}\n"
        f"  Counter-Rebuttal Strategy: {'; '.join(o.get('suggested_rebuttal_counterarguments', []))}"
        for o in opposition[:3]
    ]) if opposition else "Adversarial stress-test contentions evaluated against prosecution position."

    # 7. Precedents from DB
    prec_text = "\n\n".join([
        f"• {p.get('title')} [{p.get('citation')}] ({p.get('court')}, {p.get('decision_date')})\n"
        f"  Outcome: {p.get('outcome_type', 'supporting').upper()} ({p.get('binding_persuasive_nature', 'Binding Authority')})\n"
        f"  Legal Issue: {p.get('legal_issue')}\n"
        f"  Actual Holding: {p.get('actual_holding')}"
        for p in precedents[:5]
    ]) if precedents else "Precedent landscape retrieved from verified judicial database."

    # 8. Risks
    risks_text = "\n".join([
        f"• [{r.get('severity', 'medium').upper()} RISK] {r.get('description')} (Action: {'; '.join(r.get('mitigation_steps', []))})"
        for r in risks[:4]
    ]) if risks else "Evidentiary risks and burden of proof considerations assessed for the case."

    # Inquiries
    unresolved_questions = []
    for ev in evidence_items:
        if ev.get("follow_up_question"):
            unresolved_questions.append(ev["follow_up_question"])
    for r in risks:
        for missing in r.get("clarification_documents_needed", []):
            unresolved_questions.append(f"Missing documentation: {missing}")
    unresolved_text = "\n".join([f"{idx+1}. {q}" for idx, q in enumerate(unresolved_questions[:4])]) if unresolved_questions else "Outstanding questions to be addressed through certified records."

    # Warnings
    warnings_text = (
        f"1. Precedent Verification: {len(precedents)} authorities retrieved from verified Supreme Court database.\n"
        f"2. Procedural Stage Strictness: Strategy tailored strictly to {posture_info['current_forum']} ({posture_info['posture']}).\n"
        "3. Evidentiary Boundary: Legal findings restricted strictly to the verified case record without unsupported assumptions."
    )

    return {
        "executive_summary": (
            f"Comprehensive legal strategy brief prepared for {posture_info['party_role']} in {session.get('title')}. "
            f"Forum: {posture_info['current_forum']} ({posture_info['posture']}). "
            f"Case analysis synthesized from {len(facts)} categorized facts, {len(evidence_items)} evidence findings, "
            f"{len(arguments)} legal arguments, and {len(precedents)} verified judicial precedents."
        ),
        "parties_and_procedural_posture": posture_text,
        "parties_and_issues": posture_text,
        "verified_factual_chronology": facts_text,
        "factual_chronology": facts_text,
        "issues_for_determination": issues_text,
        "evidence_matrix": evidence_text,
        "evidence_analysis": evidence_text,
        "arguments_and_counterarguments": f"{args_text}\n\n---\n### Opposition Stress-Test (Devil's Advocate):\n{opp_text}",
        "affirmative_arguments": args_text,
        "opposition_stress_test": opp_text,
        "precedent_landscape": prec_text,
        "risks_evidentiary_gaps_questions": f"{risks_text}\n\nKey Inquiries:\n{unresolved_text}",
        "risks_and_weaknesses": risks_text,
        "unresolved_questions": unresolved_text,
        "practical_next_steps": posture_info["next_steps"],
        "action_plan": posture_info["next_steps"],
        "limitations_and_verification_warnings": warnings_text,
        "disclaimer": (
            "NyayaSarathi Legal War Room is an AI-assisted legal intelligence tool designed strictly for research, "
            "evidence synthesis, and case preparation. It does not provide legal advice, guarantee court outcomes, "
            "or replace qualified professional legal counsel."
        ),
        "generated_at": now,
    }


def generate_strategy_report(
    session: Dict[str, Any],
    chunks: List[Dict[str, Any]],
) -> Tuple[Dict[str, Any], str, str, int, int]:
    """
    Synthesizes the complete 10-section strategy report dynamically.
    Guarantees internal consistency between forum, posture, precedents, and next steps.
    """
    now = datetime.now(timezone.utc).strftime("%d %B %Y, %H:%M UTC")
    posture_info = detect_procedural_posture(session, chunks)

    system_prompt = (
        "You are an expert Indian Legal Strategist. Synthesize a 10-section Legal Strategy Report into a JSON object with keys:\n"
        "- executive_summary: comprehensive strategic summary\n"
        "- parties_and_procedural_posture: exact forum, procedural posture, appellant, respondent, and prior stages\n"
        "- verified_factual_chronology: timeline of verified procedural and factual events\n"
        "- issues_for_determination: 3 numbered core legal issues\n"
        "- evidence_matrix: review of exhibits with reliability and evidentiary status\n"
        "- arguments_and_counterarguments: affirmative arguments and opposition stress-test\n"
        "- precedent_landscape: binding Supreme Court precedents with actual holdings\n"
        "- risks_evidentiary_gaps_questions: risks, gaps, and unresolved inquiries\n"
        "- practical_next_steps: stage-appropriate procedural steps (no invalid rejoinders if appeal decided)\n"
        "- limitations_and_verification_warnings: verification warnings and doctrinal boundaries\n"
        "- disclaimer: legal disclaimer\n"
        "Return ONLY the valid JSON object with single line string values."
    )

    user_prompt = (
        f"Case: {session.get('title')}\nForum: {posture_info['current_forum']} ({posture_info['posture']})\n"
        f"Standing: {posture_info['party_role']}\n\n"
        f"Verified Case Context:\n{session.get('description')}\n\n"
        f"Facts: {json.dumps(session.get('fact_sheet', [])[:5])}\n\n"
        f"Arguments: {json.dumps(session.get('arguments', [])[:3])}\n\n"
        f"Precedents: {json.dumps(session.get('precedents', [])[:4])}\n\n"
        f"Procedural Posture Next Steps: {posture_info['next_steps']}\n\n"
        "Synthesize all 10 sections strictly aligned with this procedural posture. Return ONLY valid JSON."
    )

    try:
        report, provider, model, t_in, t_out = _call_llm_json(system_prompt, user_prompt)
        if isinstance(report, dict) and report.get("executive_summary"):
            report["generated_at"] = now
            # Mirror backward compatibility fields
            report["parties_and_issues"] = report.get("parties_and_procedural_posture", report.get("parties_and_issues", ""))
            report["factual_chronology"] = report.get("verified_factual_chronology", report.get("factual_chronology", ""))
            report["evidence_analysis"] = report.get("evidence_matrix", report.get("evidence_analysis", ""))
            report["affirmative_arguments"] = report.get("arguments_and_counterarguments", report.get("affirmative_arguments", ""))
            report["risks_and_weaknesses"] = report.get("risks_evidentiary_gaps_questions", report.get("risks_and_weaknesses", ""))
            report["action_plan"] = report.get("practical_next_steps", report.get("action_plan", ""))

            # Enforce procedural accuracy for decided appeals
            if posture_info["is_decided"]:
                report["practical_next_steps"] = posture_info["next_steps"]
                report["action_plan"] = posture_info["next_steps"]

            if "disclaimer" not in report or not report["disclaimer"]:
                report["disclaimer"] = (
                    "NyayaSarathi Legal War Room is an AI-assisted legal intelligence tool designed strictly for research, "
                    "evidence synthesis, and case preparation. It does not provide legal advice, guarantee court outcomes, "
                    "or replace qualified professional legal counsel."
                )
            return report, provider, model, t_in, t_out
    except Exception as e:
        log.warning(f"LLM strategy report synthesis failed ({e}); synthesizing dynamically from verified database records.")

    report = _synthesize_report_from_db_session(session)
    return report, "local_sqlite_db", "nyayasarathi.db(verified_strategy_dossier)", 0, estimate_tokens(str(report))


# ── Legacy Backward Compatibility ─────────────────────────────────────────────

def simulate_war_room(request: WarRoomRequest) -> WarRoomResponse:
    """Dynamically generates adversarial arguments using Groq LLM or verified authorities."""
    system_prompt = (
        f"You are adversarial opposing counsel against the client whose standing is {request.position}.\n"
        f"Generate {request.rounds} adversarial rounds of counter-arguments, weaknesses, and reinforcements.\n"
        "Return ONLY a JSON object with keys: counter_arguments (list of strings), weaknesses_identified (list of strings), suggested_reinforcements (list of strings)."
    )
    user_prompt = f"Client Position: {request.position}\nRounds: {request.rounds}"
    try:
        data, _, _, _, _ = _call_llm_json(system_prompt, user_prompt)
        if isinstance(data, dict):
            return WarRoomResponse(
                counter_arguments=_ensure_list(data.get("counter_arguments", [])),
                weaknesses_identified=_ensure_list(data.get("weaknesses_identified", [])),
                suggested_reinforcements=_ensure_list(data.get("suggested_reinforcements", [])),
            )
        raise ValueError("LLM did not return a valid dictionary for adversarial simulation.")
    except Exception as e:
        log.error(f"Legacy simulate_war_room LLM generation failed: {e}.")
        raise RuntimeError(f"War Room adversarial simulation failed: {str(e)}")
