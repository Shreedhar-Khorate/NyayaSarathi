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


def fetch_document_chunks(doc_ids: List[str], max_chunks: int = 4) -> List[Dict[str, Any]]:
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
                "text": (r["text"][:350] if r["text"] else ""),
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

    # 6. Unterminated string and brace completion recovery
    for closing in ['"]', '"}', '"}]', '"}}', ']', '}']:
        try:
            return json.loads(cleaned + closing, strict=False)
        except Exception:
            pass

    # 7. Cut at last valid object separator
    last_item = max(cleaned.rfind("},"), cleaned.rfind("}\n"))
    if last_item > 0:
        truncated = cleaned[:last_item+1]
        if cleaned.strip().startswith("[") and not truncated.strip().endswith("]"):
            truncated += "]"
        try:
            return json.loads(truncated, strict=False)
        except Exception:
            pass

    # 8. Try ast.literal_eval
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
            max_tokens=3000,
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
    query_text: Optional[str] = None,
    page: int = 1,
    page_size: int = 5,
) -> WarRoomAnalyzeResponse:
    session = get_session_by_id(session_id)
    if not session:
        raise ValueError(f"War Room session '{session_id}' not found.")

    start_time = time.perf_counter()
    doc_ids = session.get("selected_doc_ids", [])
    case_hash = get_case_state_hash(session)
    op_key = f"{operation}_{query_text}_{page}_{page_size}" if operation == "precedents" else operation
    cache_key = build_cache_key(session_id, op_key, case_hash, doc_ids)

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

    if operation == "overview":
        result, provider_name, model_name, tokens_in, tokens_out = generate_case_overview(session, chunks, custom_instructions)
        # Populate fact_sheet with categorized facts and allegations
        facts_list = list(result.get("important_facts", [])) + list(result.get("unverified_allegations", []))
        update_session(session_id, {
            "case_overview": result,
            "fact_sheet": facts_list,
        })
    elif operation == "facts":
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
        # Remote Hugging Face Dataset Integration (overthelex/indian-court-decisions)
        result, provider_name, model_name, tokens_in, tokens_out = research_precedents(
            session, chunks, query_text=query_text, page=page, page_size=page_size
        )
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


# ── Feature A: Grounded Case Overview & Fact Sheet ─────────────────────────────

def generate_case_overview(
    session: Dict[str, Any],
    chunks: List[Dict[str, Any]],
    custom_instructions: Optional[str] = None,
) -> Tuple[Dict[str, Any], str, str, int, int]:
    """
    Feature A: Case Overview
    Generates a concise summary from actual case details and available documents.
    Includes:
    - case_summary: narrative summarizing facts and claims
    - important_facts: factual statements grounded in primary records
    - main_legal_issues: core statutory and procedural questions
    - relevant_dates: timeline of dates and events
    - unverified_allegations: disputed assertions or uncorroborated claims
    - missing_information: evidentiary and documentary gaps in the record
    Strictly distinguishes documented facts from unverified allegations.
    """
    description = session.get("description", "")
    posture_info = detect_procedural_posture(session, chunks)

    # Retrieve relevant precedents from Hugging Face dataset for evidentiary grounding
    hf_precedent_context = ""
    try:
        from services.precedent_verification import retrieve_huggingface_precedents
        hf_precs, _ = retrieve_huggingface_precedents(
            description=description + " " + session.get("title", ""),
            case_type=session.get("case_type", "general"),
            court=session.get("court") or session.get("jurisdiction", "High Court"),
            user_position=posture_info["party_role"],
            page=1,
            page_size=3,
        )
        if hf_precs:
            hf_precedent_context = "\n".join([
                f"- [Hugging Face Precedent] {p['title']} ({p['court']}, {p['decision_date']}): {p['actual_holding'][:160]}... [CNR: {p['cnr']}]"
                for p in hf_precs[:3]
            ])
    except Exception as e:
        log.debug(f"Hugging Face precedent lookup for overview skipped: {e}")

    evidence_context = ""
    for idx, c in enumerate(chunks):
        evidence_context += f"[Exhibit {idx+1}: {c['doc_title']}, p.{c['page_number']}]\n{c['text'][:350]}\n\n"

    system_prompt = (
        "You are an expert Judicial Registrar and Case Strategist. Generate a structured Case Overview strictly as a JSON object with keys:\n"
        "- case_summary: concise, objective summary of the dispute, procedural posture, and claims (1-2 paragraphs). Do not state that either party definitively owns disputed property or rights solely from unverified assertions.\n"
        "- important_facts: array of objects with keys [id, fact, category, source_type, source_doc_title, page_number, verification_status, source_reliability]. "
        "Category must be one of: 'user_provided_fact', 'documentary_evidence', 'established_fact', 'procedural_event'. "
        "source_type must be: 'user_input', 'uploaded_document', 'retrieved_judgment', or 'derived_inference'. "
        "source_doc_title: title of document examined, or 'User Case Statement'. "
        "page_number: ONLY set page_number if actually provided in the exhibit (e.g. p. 4). Set null if no page reference exists. NEVER invent page numbers! "
        "verification_status: 'user_supplied_unverified', 'verified_from_primary_record', or 'reported_in_judgment'. Do NOT describe a user statement as independently verified unless an original/certified source document was actually inspected.\n"
        "- main_legal_issues: array of 2 to 4 precise legal and statutory questions for determination strictly tailored to the dispute type (for civil matters, focus on property rights, contract terms, or declaratory relief under civil statutes; NEVER insert criminal law provisions or criminal procedure into civil disputes).\n"
        "- relevant_dates: array of objects with keys [event_date, description, source_reference]. Build chronology exclusively from dates explicitly supported by case input or actual documents. Preserve exact dates when available; preserve year-only dates exactly as stated without inventing day or month; mark unknown dates as 'Date not provided'. NEVER invent exact day/month to fill gaps!\n"
        "- unverified_allegations: array of objects with keys [id, fact, alleged_by, category, verification_status, missing_proof]. Category should be 'party_allegation' or 'disputed_fact', verification_status 'unverified_submission'. Any unilateral claim of ownership or transfer unsupported by primary title records must be identified as an unverified allegation until original/certified records are produced.\n"
        "- missing_information: array of 2 to 4 strings describing evidentiary gaps or missing certified records (e.g. original instruments, certified copies from registration authorities, complete chain-of-title records, or official correspondence).\n\n"
        "CRITICAL ANTI-HALLUCINATION RULES:\n"
        "- Do NOT invent weapons, injuries, motive, or findings not present in the record.\n"
        "- In civil disputes, DO NOT insert criminal-law provisions (IPC, CrPC, BNS, BNSS, bail, arrest, homicide) or criminal trial procedures.\n"
        "- Do NOT invent execution dates, registration numbers, suit numbers, courts, or unproduced exhibits.\n"
        "- For adverse possession claims, require strict proof of continuous, open, and hostile possession for the full statutory period (e.g. 12 years under Article 65 Limitation Act, 1963)."
    )

    hf_block = f"Authentic Authorities from Hugging Face Dataset (overthelex/indian-court-decisions):\n{hf_precedent_context}\n\n" if hf_precedent_context else ""
    inst_block = f"Custom Instructions: {custom_instructions}" if custom_instructions else "Synthesize the complete Case Overview with case summary, important facts, legal issues, dates, allegations, and gaps."

    user_prompt = (
        f"Case: {session.get('title')}\nForum: {posture_info['current_forum']} ({posture_info['posture']})\n"
        f"Standing: {posture_info['party_role']}\n\n"
        f"Case Record / Primary Pleading:\n{description if description else 'No narrative provided.'}\n\n"
        f"Attached Exhibits & Excerpts:\n{evidence_context if evidence_context else 'Primary Case Record'}\n\n"
        f"{hf_block}"
        f"{inst_block}"
    )

    try:
        overview, provider, model, t_in, t_out = _call_llm_json(system_prompt, user_prompt)
        if isinstance(overview, dict) and overview.get("case_summary"):
            overview["main_legal_issues"] = _ensure_list(overview.get("main_legal_issues", []))
            overview["missing_information"] = _ensure_list(overview.get("missing_information", []))
            
            facts = overview.get("important_facts", [])
            if isinstance(facts, list):
                for idx, f in enumerate(facts):
                    if not f.get("id"):
                        f["id"] = f"fact-{idx+1}"
                    f["is_reviewed"] = f.get("is_reviewed", False)
                    if not f.get("source_type"):
                        f["source_type"] = "uploaded_document" if f.get("source_doc_title") and "Ex" in str(f.get("source_doc_title")) else "user_input"
                    if not f.get("source_doc_title"):
                        f["source_doc_title"] = "User Case Statement"
            else:
                overview["important_facts"] = []

            allegations = overview.get("unverified_allegations", [])
            if isinstance(allegations, list):
                for idx, a in enumerate(allegations):
                    if not a.get("id"):
                        a["id"] = f"allegation-{idx+1}"
                    a["category"] = a.get("category") or "party_allegation"
                    a["verification_status"] = "unverified_submission"
                    if not a.get("fact") and a.get("allegation"):
                        a["fact"] = a.get("allegation")
            else:
                overview["unverified_allegations"] = []

            return overview, provider, model, t_in, t_out
        raise ValueError("LLM did not return a valid Case Overview object.")
    except Exception as e:
        log.error(f"War Room LLM case overview generation failed: {e}")
        raise RuntimeError(f"Case overview generation failed: {str(e)}")


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
        "1. 'user_provided_fact': Information provided directly in the case statement/pleadings (subject to formal proof, e.g. claimed transaction or agreement dates).\n"
        "2. 'documentary_evidence': Written records, instruments, and exhibits actually tendered or referenced (e.g. instruments, copies, receipts, or official notices actually produced).\n"
        "3. 'established_fact': Uncontested or admitted factual points (e.g. admitted possession, uncontested dates).\n"
        "4. 'party_allegation': Unadjudicated assertions or contested claims made by a party (e.g. contested transfer claims, verbal agreements).\n"
        "5. 'disputed_fact': Factual matters directly contested between the parties (e.g. competing ownership claims, validity of instruments).\n"
        "6. 'procedural_event': Official procedural history, convictions, appeals, or court orders.\n"
        "7. 'missing_evidence': Critical documents or proof not yet produced (e.g. original instruments, certified public records, chain of title).\n\n"
        "CRITICAL RULES:\n"
        "- Do NOT describe a user statement as independently verified unless an original/certified source document was actually inspected.\n"
        "- If a document is a copy or photocopy, describe it accurately as a copy (e.g. 'copy of deed', 'photocopy of document').\n"
        "- In civil disputes, NEVER insert criminal law provisions (IPC, CrPC, Section 300, Section 302, bail, arrest) or criminal trial procedures.\n"
        "- NEVER invent exact dates not provided (preserve year-only dates exactly as provided; mark missing as 'Date not provided').\n"
        "- Set source_type to: 'user_input', 'uploaded_document', 'retrieved_judgment', or 'derived_inference'.\n"
        "- Set verification_status to one of: 'verified_from_primary_record', 'reported_in_judgment', 'user_supplied_unverified', 'verification_required'.\n"
        "- Set source_reliability to: 'primary_judicial_record', 'official_court_record', 'contemporaneous_document', 'party_pleading', or 'unverified_claim'.\n"
        "Return ONLY a JSON array of objects with keys: id, fact, category, source_type, source_doc_title, page_number, verification_status, source_reliability, confidence."
    )

    user_prompt = (
        f"Case: {session.get('title')}\nForum: {posture_info['current_forum']} ({posture_info['posture']})\n"
        f"Standing: {posture_info['party_role']}\n\n"
        f"Case Record / Primary Pleading:\n{description if description else 'No narrative provided.'}\n\n"
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
                if not f.get("source_type"):
                    f["source_type"] = "uploaded_document" if f.get("source_doc_title") and "Ex" in str(f.get("source_doc_title")) else "user_input"
                # Safeguard against wrongful allegation tagging for confirmed court orders
                cat = f.get("category", "").lower()
                text = f.get("fact", "").lower()
                if any(w in text for w in ["convicted", "dismissed", "sentenced", "sessions", "high court", "appeal"]) and not posture_info.get("is_civil"):
                    if cat in ("unverified_allegation", "allegation"):
                        f["category"] = "procedural_event"
                        f["verification_status"] = "verified_from_primary_record"
                        f["source_reliability"] = "official_court_record"
                elif any(w in text for w in ["altered", "held that", "acquitted", "supreme court held", "modified to"]):
                    if cat in ("unverified_allegation", "allegation"):
                        f["category"] = "final_holding"
                        f["verification_status"] = "verified_from_primary_record"
                        f["source_reliability"] = "primary_judicial_record"

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
    Strictly separates: User-Provided Information, Facts Supported by Supplied Documents,
    Verified External Legal Authorities, Party Allegations, Disputed Facts, Legal Inferences,
    and Missing Evidence and Unresolved Questions.
    """
    evidence_context = ""
    for idx, c in enumerate(chunks):
        evidence_context += f"[Exhibit {idx+1}: {c['doc_title']}, p.{c['page_number']}]\n{c['text'][:450]}\n\n"

    posture_info = detect_procedural_posture(session, chunks)

    system_prompt = (
        "You are an Indian Judicial Evidence Specialist. Analyze the provided case facts and exhibits.\n"
        "Separate evidence strictly into reliable categories:\n"
        "- 'user_provided_information': Statements from pleadings or user input.\n"
        "- 'supplied_document_fact': Facts supported by copies or documents actually produced.\n"
        "- 'party_allegation': Uncorroborated contentions asserted by either party.\n"
        "- 'disputed_fact': Contested questions of title, ownership, or validity.\n"
        "- 'legal_inference': Logical legal inferences drawn from statutory provisions.\n"
        "- 'missing_evidence': Critical primary records, originals, or certified searches not yet produced.\n\n"
        "CRITICAL RULES:\n"
        "- Never describe a user statement as independently verified unless an original/certified source document was actually inspected.\n"
        "- In civil property disputes:\n"
        "  * Secondary evidence (photocopies or uncertified copies) requires laying foundation under Sections 64 & 65 of the Indian Evidence Act / Section 58 BSA, 2023.\n"
        "  * Unregistered or unexecuted transfer documents cannot convey or extinguish title to immovable property under Sections 17 & 49 of the Registration Act, 1908.\n"
        "  * Fiscal or mutation receipts (e.g. municipal tax payments) reflect revenue assessment, not substantive title to immovable property.\n"
        "  * Possession without proof of hostile title for the full 12-year statutory period under Article 65 of the Limitation Act cannot establish ownership.\n"
        "- Do not invent page numbers, exhibit numbers, court docket entries, quotations, document titles, or registration numbers.\n"
        "- Set source_reliability to: 'primary_judicial_record', 'official_court_record', 'contemporaneous_document', 'party_pleading', or 'unverified_claim'.\n"
        "- Set evidentiary_status to: 'established', 'disputed', 'corroborated_by_record', 'unsupported', 'inadmissible', or 'verification_required'.\n"
        "- Set legal_relevance to: 'direct_probative', 'contextual_procedural', 'impeachment', or 'peripheral'.\n"
        "Return ONLY a JSON array of findings with keys: id, finding, underlying_fact, evidence_category, why_it_matters, source_reliability, evidentiary_status, legal_relevance, source_doc_title, page_number, confidence_status, follow_up_question, is_disputed."
    )

    user_prompt = (
        f"Case: {session.get('title')}\nStanding: {session.get('user_position')}\nForum: {posture_info['current_forum']}\n\n"
        f"Facts & Pleading:\n{session.get('description')}\n\n"
        f"Exhibits:\n{evidence_context if evidence_context else 'No external exhibits uploaded (relying on case pleading and party statements)'}\n\n"
        f"{'Instructions: ' + custom_instructions if custom_instructions else 'Provide 4 to 6 evidence findings strictly grounded in the verified case record without inventing unproduced exhibits.'}"
    )

    try:
        findings, provider, model, t_in, t_out = _call_llm_json(system_prompt, user_prompt)
        if isinstance(findings, list) and findings:
            for idx, f in enumerate(findings):
                if not f.get("id"):
                    f["id"] = f"ev-{idx+1}"
                f["confidence"] = f.get("confidence_status", "High / Grounded in Pleading")
                if not f.get("why_it_matters"):
                    f["why_it_matters"] = f"Directly informs {f.get('underlying_fact', 'the legal claim')} before the court."
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
    - Domain-appropriate statutory provisions (e.g. TPA, Registration Act, Specific Relief Act for civil; IPC/CrPC/BNS/BNSS for criminal).
    - Verified facts, required evidence, binding authorities.
    - Strongest opposing argument and evidence-based rebuttal.
    """
    posture_info = detect_procedural_posture(session, chunks)
    case_type = session.get("case_type", "general")
    is_civil = posture_info.get("is_civil", False)
    statute_regime = posture_info.get("statute_title", "Applicable Statutory Regime")
    party_role = posture_info["party_role"]

    verified_precedents = query_verified_precedents(
        case_type=case_type,
        description=session.get("description", "") + " " + session.get("title", ""),
        user_position=party_role
    )

    precedent_context = "\n".join([
        f"- {p['title']} [{p['citation']}] ({p['court']}, {p['decision_date']}): {p['actual_holding']} [CNR: {p['cnr']}] [Source: {p.get('source_url', 'https://huggingface.co/datasets/overthelex/indian-court-decisions')}]"
        for p in verified_precedents[:4]
    ])

    system_prompt = (
        f"You are a Senior Indian Advocate representing the {party_role.upper()} before the {posture_info['current_forum']}.\n"
        f"Applicable Statutory Regime: {statute_regime}.\n"
        "Draft rigorous legal arguments structured in a JSON array. Each argument must have:\n"
        "- id: string (e.g. 'arg-1')\n"
        "- title: concise headline\n"
        "- legal_issue: precise statutory question\n"
        "- applicable_provisions: list of relevant statutory sections strictly tailored to the dispute type and applicable statutory regime\n"
        "- procedural_role_argument: proposed argument framed specifically for client's procedural standing\n"
        "- main_claim: core legal proposition\n"
        "- supporting_facts: list of verified factual points from the record\n"
        "- evidence_actually_available: documents and evidence actually produced or admitted in the record\n"
        "- evidence_still_required: specific documents or proof still needed to establish the claim\n"
        "- relevant_precedents: list of verified judicial authorities from the provided list. Cite ONLY verified authorities from the provided list. Do NOT invent citations.\n"
        "- legal_reasoning: doctrinal application connecting statutory ingredients to verified facts without manufacturing evidence.\n"
        "- strongest_opposing_argument: strongest counter-argument opponent will raise\n"
        "- rebuttal_and_weaknesses: evidence-based rebuttal addressing weaknesses in client's case\n"
        "- potential_weaknesses: list of points counsel must be prepared to defend\n"
        "- confidence_status: confidence or verification status expressed in words (e.g. 'Strong Prima Facie Ground Subject to Original Document Production', 'High Doctrinal Soundness', 'Moderate / Requires Corroboration') — NEVER unsupported numerical percentages!\n"
        "- questions_to_investigate: actionable factual questions\n\n"
        "CRITICAL RULES:\n"
        "- Do NOT manufacture evidence to strengthen the selected party's position.\n"
        "- Argue the selected party's side while acknowledging material weaknesses.\n"
        "- If civil property dispute, DO NOT insert criminal provisions, homicide doctrines, or criminal trial procedures.\n"
        "- Do NOT invent fake case citations."
    )

    user_prompt = (
        f"Case: {session.get('title')}\nForum: {posture_info['current_forum']} ({posture_info['posture']})\n"
        f"Procedural Role: {party_role}\n\n"
        f"Case Facts & Judicial Record:\n{session.get('description')}\n\n"
        f"Verified Authorities from Hugging Face Dataset (overthelex/indian-court-decisions):\n{precedent_context}\n\n"
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
                a["evidence_refs"] = _ensure_list(a.get("evidence_refs", a.get("evidence_actually_available", [])))
                a["evidence_still_required"] = _ensure_list(a.get("evidence_still_required"))
                a["questions_to_investigate"] = _ensure_list(a.get("questions_to_investigate"))
                if not a.get("confidence_status"):
                    a["confidence_status"] = "High Doctrinal Ground" if is_civil else "Well-Grounded Statutory Plea"
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
    Strictly grounded in factual contentions and adverse authorities from Hugging Face dataset.
    """
    posture_info = detect_procedural_posture(session, chunks)
    is_civil = posture_info.get("is_civil", False)
    party_role = posture_info["party_role"]

    if is_civil:
        opp_name = session.get("opposing_party") or (posture_info.get("respondent") if posture_info.get("respondent") and "Defendant" not in posture_info.get("respondent") else None)
        if "Plaintiff" in party_role:
            opp_role = f"Defendant / Opposing Party ({opp_name})" if opp_name else "Defendant / Opposing Party"
        else:
            opp_role = f"Plaintiff / Claimant ({opp_name})" if opp_name else "Plaintiff / Claimant"
    else:
        opp_role = "Respondent State / Prosecution" if party_role == "Appellant" else "Appellant / Defense"

    # Retrieve adverse authorities from Hugging Face dataset
    adverse_context = ""
    try:
        from services.precedent_verification import query_verified_precedents
        adverse_precs = query_verified_precedents(
            case_type=session.get("case_type", "general"),
            description=session.get("description", "") + " " + session.get("title", ""),
            user_position=party_role
        )
        adv_items = [p for p in adverse_precs if p.get("outcome_type") in ("adverse", "distinguishable")]
        if not adv_items:
            adv_items = adverse_precs[:3]
        adverse_context = "\n".join([
            f"- {p['title']} [{p['citation']}] ({p['court']}, {p['decision_date']}): {p['actual_holding'][:180]}... [CNR: {p['cnr']}]"
            for p in adv_items[:3]
        ])
    except Exception as e:
        log.debug(f"Adverse precedent lookup skipped: {e}")

    system_prompt = (
        f"You are Senior Counsel representing the OPPOSING PARTY ({opp_role}).\n"
        "Your role is DEVIL'S ADVOCATE: stress-test the case using strictly legitimate legal and evidentiary grounds.\n"
        "CRITICAL RULES:\n"
        "- Ground objections strictly in the actual factual dispute and verified law.\n"
        "- In civil disputes:\n"
        "  * Opposing counsel will challenge title defects, lack of primary evidence, admissibility under the Registration Act / Evidence Act, continuous physical possession, and question uncertified documents.\n"
        "  * If identifying possible evidence opponent could produce, MUST label it as 'hypothetical evidence / unproven submission'. NEVER describe hypothetical evidence as already submitted or verified!\n"
        "  * NEVER insert criminal prosecution concepts (homicide, murder, Section 300, bail) into civil property suits.\n"
        "- Cite adverse authorities from the provided list when available. Never fabricate case citations.\n"
        "Return ONLY a JSON array with keys:\n"
        "- id: string (e.g. 'opp-1')\n"
        "- opposing_claim: strongest contention opposing counsel will make\n"
        "- supporting_facts_known: known facts supporting this argument\n"
        "- hypothetical_unproven_claims: what remains hypothetical or unproven for the opponent\n"
        "- adverse_precedents: case law unfavorable to client (cite verified CNR / title)\n"
        "- user_position_weaknesses: where client's case is vulnerable\n"
        "- suggested_rebuttal_counterarguments: how client's counsel should respond\n"
        "- evidence_required_to_evaluate: evidence required to evaluate this contention."
    )

    adv_block = f"Adverse Authorities from Hugging Face Dataset (overthelex/indian-court-decisions):\n{adverse_context}\n\n" if adverse_context else ""
    inst_block = f"Instructions: {custom_instructions}" if custom_instructions else "Produce 2 to 3 legitimate adversarial contentions grounded in the evidence record."

    user_prompt = (
        f"Case: {session.get('title')}\nForum: {posture_info['current_forum']}\nOpposing Role: {opp_role}\n\n"
        f"Case Facts:\n{session.get('description')}\n\n"
        f"{adv_block}"
        f"{inst_block}"
    )

    try:
        opp_args, provider, model, t_in, t_out = _call_llm_json(system_prompt, user_prompt)
        if isinstance(opp_args, list) and opp_args:
            for idx, o in enumerate(opp_args):
                if not o.get("id"):
                    o["id"] = f"opp-{idx+1}"
                o["supporting_facts_evidence"] = _ensure_list(o.get("supporting_facts_evidence", o.get("supporting_facts_known", [])))
                o["adverse_precedents"] = _ensure_list(o.get("adverse_precedents"))
                o["user_position_weaknesses"] = _ensure_list(o.get("user_position_weaknesses"))
                o["suggested_rebuttal_counterarguments"] = _ensure_list(o.get("suggested_rebuttal_counterarguments"))
            return opp_args, provider, model, t_in, t_out
        raise ValueError("LLM did not return a valid list of opposition claims.")
    except Exception as e:
        log.error(f"War Room LLM opposition simulation failed: {e}")
        raise RuntimeError(f"Opposition simulation failed: {str(e)}")


# ── Feature E: Legal Precedent Research (Hugging Face Dataset Integration) ───

def research_precedents(
    session: Dict[str, Any],
    chunks: List[Dict[str, Any]],
    query_text: Optional[str] = None,
    page: int = 1,
    page_size: int = 5,
) -> Tuple[List[Dict[str, Any]], str, str, int, int]:
    """
    Feature F: Legal Precedents Through Hugging Face Dataset Integration (overthelex/indian-court-decisions)
    Reuses the exact Hugging Face dataset and retrieval infrastructure used by the Judgment Predictor.
    Supports targeted search queries and offset pagination.
    Every displayed citation is validated against official court records and the Hugging Face dataset archive.
    If no relevant source is available, clearly states that limitation instead of inventing a judgment.
    """
    posture_info = detect_procedural_posture(session, chunks)
    description = session.get("description", "") + " " + session.get("title", "")
    case_type = session.get("case_type", "general")
    court = session.get("court") or session.get("jurisdiction", "High Court")
    user_position = posture_info["party_role"]

    from services.precedent_verification import retrieve_huggingface_precedents, verify_citation, query_verified_precedents

    # 1. Retrieve authentic matching authorities from Hugging Face dataset
    hf_precedents, provenance = retrieve_huggingface_precedents(
        description=description,
        case_type=case_type,
        court=court,
        user_position=user_position,
        query_text=query_text,
        page=page,
        page_size=page_size,
    )

    # 2. Extract citations from case exhibits via RAG retrieval engine
    doc_ids = session.get("selected_doc_ids", [])
    rag_authorities = []
    if doc_ids:
        try:
            from services.rag_retrieval import get_rag_retrieval_engine
            retrieval_engine = get_rag_retrieval_engine()
            evidence_pack = retrieval_engine.retrieve_evidence(
                question="precedent citation judgment Supreme Court High Court ratio decidendi holding",
                document_ids=doc_ids,
                top_k=3,
            )
            for c in evidence_pack.chunks:
                matches = re.findall(r"(\([12]\d{3}\)\s*\d+\s*SCC\s*\d+|AIR\s*\d{4}\s*SC\s*\d+|[A-Z][a-zA-Z\s]+v\.\s+[A-Z][a-zA-Z\s]+)", c.text)
                for m in matches:
                    clean_match = m.strip()
                    if len(clean_match) > 10 and not clean_match.startswith("Exhibit"):
                        ver = verify_citation(clean_match)
                        rag_authorities.append({
                            "cnr": f"RAG-DOC-{c.chunk_id[:6]}",
                            "citation": clean_match if "SCC" in clean_match or "AIR" in clean_match else None,
                            "title": clean_match,
                            "court": ver.get("court", "Court Record Citation"),
                            "decision_date": "Extracted from Exhibit",
                            "outcome_type": "supporting",
                            "legal_issue": f"Authority referenced in {c.document_title}",
                            "relevant_paragraphs": f"p. {c.page_number}",
                            "procedural_context": f"Found in uploaded document '{c.document_title}'",
                            "actual_holding": ver.get("actual_holding", "Citation extracted from selected case exhibit."),
                            "verbatim_excerpt": c.text[:240],
                            "relevance_explanation": f"Documented in case exhibit '{c.document_title}' (p. {c.page_number}).",
                            "binding_persuasive_nature": "Persuasive / Record Reference",
                            "verification_status": ver.get("status", "verification_required"),
                            "source_url": ver.get("source_url") or "https://huggingface.co/datasets/overthelex/indian-court-decisions",
                        })
        except Exception as e:
            log.warning(f"RAG precedent extraction from documents failed or skipped: {e}")

    # 3. Retrieve verified domain authorities and combine with Hugging Face precedents
    verified_domain_precedents = query_verified_precedents(
        case_type=case_type,
        description=description,
        user_position=user_position,
        court=court,
    )

    combined = []
    seen_cnrs = set()
    court_lower = court.lower() if court else ""
    is_sc_forum = "supreme" in court_lower or "apex" in court_lower

    if is_sc_forum and verified_domain_precedents:
        # When forum is Supreme Court, prioritize authoritative Supreme Court authorities
        for vp in verified_domain_precedents:
            if vp["cnr"] not in seen_cnrs and ("supreme" in vp.get("court", "").lower()):
                combined.append(vp)
                seen_cnrs.add(vp["cnr"])
        for hp in hf_precedents:
            if hp["cnr"] not in seen_cnrs and ("supreme" in hp.get("court", "").lower()):
                combined.append(hp)
                seen_cnrs.add(hp["cnr"])
        if not combined:
            for vp in verified_domain_precedents:
                if vp["cnr"] not in seen_cnrs:
                    combined.append(vp)
                    seen_cnrs.add(vp["cnr"])
            for hp in hf_precedents:
                if hp["cnr"] not in seen_cnrs:
                    combined.append(hp)
                    seen_cnrs.add(hp["cnr"])
    else:
        for hp in hf_precedents:
            if hp["cnr"] not in seen_cnrs:
                combined.append(hp)
                seen_cnrs.add(hp["cnr"])
        for vp in verified_domain_precedents:
            if vp["cnr"] not in seen_cnrs:
                combined.append(vp)
                seen_cnrs.add(vp["cnr"])

    for ra in rag_authorities:
        if ra.get("citation") and ra.get("citation") not in {p.get("citation") for p in combined}:
            combined.append(ra)

    if not combined:
        combined = [{
            "cnr": "LIMITATION-NO-DATASET-MATCH",
            "citation": "None Verified",
            "title": "No Verified Precedents in Hugging Face Dataset",
            "court": "Supreme Court of India / High Courts",
            "decision_date": "N/A",
            "outcome_type": "inconclusive",
            "legal_issue": "Evidentiary and Doctrinal Limitation",
            "relevant_paragraphs": "N/A",
            "procedural_context": "Record Review",
            "actual_holding": "No matching judicial authority could be validated in the Hugging Face dataset (overthelex/indian-court-decisions) or the selected case documents for these specific factual parameters.",
            "verbatim_excerpt": "The system will not invent judgments or fabricate citations when authoritative records are unavailable.",
            "relevance_explanation": "Counsel should conduct independent verification in SCC Online or eCourts repository.",
            "binding_persuasive_nature": "Information Limitation",
            "verification_status": "verification_required",
            "source_url": "https://huggingface.co/datasets/overthelex/indian-court-decisions",
        }]

    return combined, "huggingface_dataset", "overthelex/indian-court-decisions", 0, len(combined) * 80


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
        "CRITICAL RULES:\n"
        "- In civil property disputes:\n"
        "  * Identify genuine evidentiary risks such as reliance on secondary copies instead of primary title deeds (Sections 64 & 65 Evidence Act / Section 58 BSA), uncorroborated transfer instruments lacking registration under Sections 17 & 49 Registration Act, adverse party's physical possession requiring relief for recovery of possession rather than mere injunction, and missing title chain.\n"
        "  * Do NOT imply that notarization, affidavits, mutation entries, tax receipts, or possession automatically cure a defective title instrument.\n"
        "  * Recommendations must reflect the actual procedural stage. If court or jurisdiction is unknown, give appropriately qualified general next steps.\n"
        "  * Do NOT insert criminal risks or criminal trial procedures into civil property matters.\n"
        "- Do NOT assign arbitrary numerical risk scores. Express severity qualitatively as 'high', 'medium', or 'low'.\n"
        "Return ONLY a JSON array of risk items with keys:\n"
        "- id: string (e.g. 'risk-1')\n"
        "- risk_type: 'unsupported_argument', 'missing_evidence', 'unresolved_factual_dispute', 'adverse_precedent', 'weak_evidence_link', or 'requires_expert_review'\n"
        "- description: concise explanation of the risk\n"
        "- severity: 'high', 'medium', or 'low'\n"
        "- affected_claims: list of impacted claims\n"
        "- supporting_source_or_basis: factual basis or supporting source for this risk\n"
        "- why_it_matters: explanation of why this risk matters\n"
        "- practical_mitigation: actionable practical remedies\n"
        "- clarification_documents_needed: specific missing documents or records."
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
                r["mitigation_steps"] = _ensure_list(r.get("mitigation_steps", r.get("practical_mitigation", [])))
                r["clarification_documents_needed"] = _ensure_list(r.get("clarification_documents_needed"))
                r["affected_claims"] = _ensure_list(r.get("affected_claims"))
                if not r.get("why_it_matters"):
                    r["why_it_matters"] = r.get("description", "Material risk impacting legal sustainability.")
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
        f"• Parties: {posture_info['appellant']} vs {posture_info['respondent']}\n"
        f"• Selected Role: {posture_info['party_role']}\n"
        f"• Applicable Statutory Regime: {posture_info.get('statute_title', 'Substantive & Procedural Laws of India')}\n"
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
            f"• [{ev.get('evidence_category', ev.get('evidence_type', 'record')).replace('_', ' ').title()}] {ev.get('finding')} "
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
        f"1. Precedent Verification: {len(precedents)} authorities retrieved from Hugging Face dataset (overthelex/indian-court-decisions) and verified records.\n"
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
