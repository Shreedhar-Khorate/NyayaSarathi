"""
Legal Draft Generator — Production AI Implementation
Generates tailored legal drafts (Legal Notices, Bail Applications, Written Statements, Petitions, etc.)
using real LLM inference with statutory grounding and optional regional language translation.
"""
from schemas.drafts import DraftRequest, DraftResponse
from services.war_room_service import _call_llm_json, _ensure_list
from logger import get_logger

log = get_logger("nyayasarathi.drafts_service")


def generate_draft(request: DraftRequest) -> DraftResponse:
    """
    Generates a formal legal draft dynamically using AI based strictly on the case facts.
    """
    system_prompt = (
        "You are an expert Indian Legal Drafting Advocate.\n"
        f"Draft a formal, professional legal document of type: '{request.draft_type}'.\n"
        "Ground the draft strictly in the provided case facts.\n"
        "Include standard Indian legal drafting headers, jurisdictional recital, factual paragraphs, "
        "applicable statutory sections and legal grounds, prayer / demand clause, and signature blocks.\n"
        "Return strictly a JSON object with keys:\n"
        "- draft_text: the complete formal legal document text\n"
        "- citations_used: list of actual statutory provisions, acts, or rules incorporated (e.g. ['Section 80 CPC', 'Section 138 NI Act'])\n"
        "- translated_text: if target_language is provided, provide the complete translation into that language; otherwise set to null."
    )

    lang_instr = f"Target Language for Translation: {request.target_language}" if request.target_language else "No translation requested."
    user_prompt = (
        f"Draft Type: {request.draft_type}\n"
        f"Case Facts:\n{request.case_facts}\n\n"
        f"{lang_instr}\n\n"
        "Draft the document now in JSON format."
    )

    try:
        data, provider, model, t_in, t_out = _call_llm_json(system_prompt, user_prompt)
        if isinstance(data, dict) and data.get("draft_text"):
            return DraftResponse(
                draft_text=str(data["draft_text"]),
                translated_text=str(data["translated_text"]) if data.get("translated_text") else None,
                citations_used=_ensure_list(data.get("citations_used", [])),
            )
    except Exception as e:
        log.error(f"AI draft generation failed: {e}")

    # Fallback to structured factual notice if API is unavailable
    draft = (
        f"{request.draft_type.upper()}\n\n"
        f"To,\n[Opposing Party / Recipient]\n\n"
        f"Subject: {request.draft_type} regarding grievance arising out of stated facts.\n\n"
        f"Sir / Madam,\n\n"
        f"Under instructions from and on behalf of my client, this formal document is drawn "
        f"based on the following factual statement:\n\n"
        f"{request.case_facts}\n\n"
        f"You are hereby called upon to address the aforesaid grievances within 15 days of receipt "
        f"of this communication, failing which my client shall be constrained to initiate appropriate "
        f"legal proceedings before the competent court of jurisdiction.\n\n"
        f"Yours faithfully,\nAdvocate for Client"
    )

    return DraftResponse(
        draft_text=draft,
        translated_text=None,
        citations_used=[],
    )
