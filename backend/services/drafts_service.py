"""
Legal Draft Generator — Sample Implementation
TODO: Replace with LLM-based draft generation + IndicTrans2 translation API.
"""
from schemas.drafts import DraftRequest, DraftResponse


def generate_draft(request: DraftRequest) -> DraftResponse:
    draft = (
        f"LEGAL NOTICE\n\n"
        f"To,\n[Recipient Name & Address]\n\n"
        f"Subject: {request.draft_type}\n\n"
        f"Under instructions from and on behalf of my client, I hereby issue this legal notice "
        f"based on the following facts:\n\n"
        f"{request.case_facts}\n\n"
        f"You are hereby called upon to remedy the above grievance within 15 days of receipt "
        f"of this notice, failing which my client shall be constrained to initiate appropriate "
        f"legal proceedings against you without further notice.\n\n"
        f"Yours faithfully,\n[Advocate Name]\n[Bar Council No.]"
    )

    return DraftResponse(
        draft_text=draft,
        translated_text=f"[Translation to '{request.target_language}' — TODO: integrate IndicTrans2 API]"
        if request.target_language
        else None,
        citations_used=[
            "Section 80, Code of Civil Procedure (mandatory notice for suits against Govt.)",
            "Section 138, Negotiable Instruments Act (if cheque dishonour is involved)",
        ],
    )
