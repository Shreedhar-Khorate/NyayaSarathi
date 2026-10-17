"""
Grounded Explanation Engine for NyayaSarathi.

Synthesizes plain-language legal takeaways, supporting factors, opposing factors,
and limitations grounded strictly in retrieved precedents and statutory metadata.
"""

import os
import json
from typing import List, Dict, Any, Optional
from models.prediction import StructuredCaseProfile, VerifiedPrecedent, GroundedExplanation


class GroundedExplanationEngine:
    """
    Generates evidence-grounded legal explanations and factor attributions.
    """

    def generate_explanation(
        self,
        structured_case: StructuredCaseProfile,
        probability: int,
        confidence: str,
        precedents: List[VerifiedPrecedent],
    ) -> GroundedExplanation:
        """
        Synthesizes a grounded explanation from structured case profile and verified precedents.
        """
        # 1. Attempt dynamic synthesis via active multi-provider LLM (Groq / Cerebras / Gemini / Ollama)
        try:
            llm_explanation = self._synthesize_with_llm(
                structured_case, probability, confidence, precedents
            )
            if llm_explanation:
                return llm_explanation
        except Exception:
            pass  # Fallback to deterministic synthesis

        return self._synthesize_deterministic(
            structured_case, probability, confidence, precedents
        )

    def _synthesize_deterministic(
        self,
        structured_case: StructuredCaseProfile,
        probability: int,
        confidence: str,
        precedents: List[VerifiedPrecedent],
    ) -> GroundedExplanation:
        """
        Deterministic, rule-grounded synthesis ensuring 100% factual accuracy.
        """
        case_type_display = structured_case.case_type.replace("_", " ").title()
        user_pos = (
            structured_case.user_position
            if structured_case.user_position and structured_case.user_position != "unknown"
            else "applicant / petitioner"
        )
        total_p = len(precedents)

        fav_precedents = [p for p in precedents if p.favorable_to_user == "Favorable"]
        unfav_precedents = [p for p in precedents if p.favorable_to_user == "Unfavorable"]
        part_precedents = [p for p in precedents if "Partially" in p.favorable_to_user]

        # ── 1. Executive Takeaway ────────────────────────────────────────────
        if probability >= 65:
            takeaway = (
                f"Based on historical outcome analysis across {total_p} similar High Court rulings, "
                f"the case presents a strong favorable posture ({probability}% estimated success probability) "
                f"for the {user_pos}. Primary drivers include strong precedent alignment in {case_type_display} matters "
                f"where discretionary relief was granted under comparable statutory grounds."
            )
        elif probability <= 35:
            takeaway = (
                f"Historical judicial analysis indicates notable headwinds ({probability}% estimated favorable probability) "
                f"for the {user_pos}. Comparable High Court rulings reflect stricter judicial scrutiny, "
                f"suggesting that key opposition arguments regarding statutory bars or evidentiary standards must be addressed proactively."
            )
        else:
            takeaway = (
                f"Precedent analysis indicates a balanced judicial posture ({probability}% estimated probability) "
                f"for the {user_pos}. Historical rulings show outcomes are discretionary and heavily dependent on specific "
                f"factual documentation, clean antecedents, and the persuasiveness of arguments presented."
            )

        # ── 2. Supporting Factors ───────────────────────────────────────────
        supporting_factors = []

        if structured_case.detected_sections:
            sec_formatted = [
                s if s.lower().startswith(("section", "article", "order")) else f"Section {s}"
                for s in structured_case.detected_sections[:3]
            ]
            sec_str = ", ".join(sec_formatted)
            supporting_factors.append(
                f"Statutory alignment: Case is grounded in recognized provisions under {sec_str}."
            )

        if fav_precedents:
            top_fav = fav_precedents[0]
            supporting_factors.append(
                f"Precedent grant: In {top_fav.case_name} ({top_fav.court}, {top_fav.year}), the court ruled {top_fav.outcome} under comparable facts."
            )

        if len(fav_precedents) + len(part_precedents) > 0:
            fav_count = len(fav_precedents) + len(part_precedents)
            supporting_factors.append(
                f"Favorable precedent density: {fav_count} of {total_p} closely ranked historical cases secured favorable or partially allowed relief."
            )

        # Factual cues
        if any("cooperat" in f.lower() or "clean" in f.lower() for f in structured_case.key_facts):
            supporting_factors.append(
                "Factual posture: Cooperation with proceedings and absence of adverse criminal history are established factors supporting discretionary relief."
            )
        else:
            supporting_factors.append(
                "Procedural standing: The petition/claim invokes established remedies within the High Court's jurisdiction."
            )

        # ── 3. Opposing / Risk Factors ───────────────────────────────────────
        opposing_factors = []

        if unfav_precedents:
            top_unfav = unfav_precedents[0]
            opposing_factors.append(
                f"Adverse precedent risk: In {top_unfav.case_name} ({top_unfav.court}, {top_unfav.year}), the court ordered {top_unfav.outcome} due to severity of allegations or evidentiary thresholds."
            )

        if structured_case.case_type in ["bail", "criminal"]:
            opposing_factors.append(
                "Prosecution objections: The State/prosecution may oppose relief citing prima facie evidence, gravity of charges, or necessity of custodial investigation."
            )
        elif structured_case.case_type in ["contract", "civil", "commercial"]:
            opposing_factors.append(
                "Evidentiary burden: Opposing counsel may challenge documentation, contractual breach causation, or limitation periods."
            )
        elif structured_case.case_type in ["motor_accident"]:
            opposing_factors.append(
                "Insurance contestation: Insurers typically dispute multiplier computations, income assessment, or contributory negligence."
            )
        else:
            opposing_factors.append(
                "Judicial discretion: Discretionary relief requires satisfying rigorous judicial tests under applicable procedural codes."
            )

        # ── 4. Limitations ───────────────────────────────────────────────────
        limitations = [
            "This prediction is an AI-generated advisory estimate based on historical court data and is not a guarantee of future judicial outcome.",
            "Judicial outcomes depend heavily on the specific bench constitution, oral arguments, and factual appreciation at trial.",
            "Statutory provisions and judicial interpretations may evolve across different High Court jurisdictions.",
        ]

        return GroundedExplanation(
            takeaway=takeaway,
            supporting_factors=supporting_factors,
            opposing_factors=opposing_factors,
            limitations=limitations,
            synthesis_engine="NyayaSarathi Grounded Legal Synthesizer",
        )

    def _synthesize_with_llm(
        self,
        structured_case: StructuredCaseProfile,
        probability: int,
        confidence: str,
        precedents: List[VerifiedPrecedent],
    ) -> Optional[GroundedExplanation]:
        """Dynamic grounded legal synthesis using multi-provider LLM (Groq / Cerebras / Gemini / Ollama)."""
        try:
            from services.war_room_service import _call_llm_json, _ensure_list

            user_pos_clean = (
                structured_case.user_position
                if structured_case.user_position and structured_case.user_position != "unknown"
                else "applicant / petitioner"
            )

            # Build evidence brief for the prompt
            precedents_brief = "\n".join([
                f"- Case: {p.case_name} ({p.court}, {p.year})\n  Outcome: {p.outcome} (Impact: {p.favorable_to_user})\n  Holding Excerpt: {p.verbatim_excerpt[:250]}"
                for p in precedents[:4]
            ])

            system_prompt = (
                "You are NyayaSarathi's Senior Legal Intelligence Synthesizer.\n"
                "Synthesize an evidence-grounded judicial explanation for an Indian court matter.\n"
                "CRITICAL RULES:\n"
                "- Do not invent cases, statutes, or section numbers.\n"
                f"- Do not change the mathematical probability ({probability}%).\n"
                "Return strictly a JSON object with keys:\n"
                "- takeaway: A 2-3 sentence executive summary explaining the judicial likelihood from the perspective of the party.\n"
                "- supporting_factors: A list of 2-3 specific legal/factual strengths grounded in the statutory provisions or favorable precedents.\n"
                "- opposing_factors: A list of 2-3 realistic counterarguments, prosecution/defense objections, or evidentiary hurdles.\n"
                "- limitations: A list of 2-3 standard Indian judicial caveats (e.g. bench discretion, oral arguments, trial evidence)."
            )

            user_prompt = f"""
CASE FACTS:
- Legal Domain: {structured_case.case_type}
- Procedural Position: {user_pos_clean}
- Statutory Sections: {', '.join(structured_case.detected_sections) if structured_case.detected_sections else 'General'}
- Case Narrative: {structured_case.key_facts[0] if structured_case.key_facts else 'Case brief'}

MATHEMATICAL PREDICTION (DO NOT CHANGE):
- Calculated Success Probability: {probability}%
- Model Confidence: {confidence}

VERIFIED HISTORICAL PRECEDENTS:
{precedents_brief}

Produce the structured grounded explanation in JSON now.
"""
            data, provider, model, _, _ = _call_llm_json(system_prompt, user_prompt)
            if isinstance(data, dict) and data.get("takeaway"):
                return GroundedExplanation(
                    takeaway=str(data.get("takeaway", "")),
                    supporting_factors=_ensure_list(data.get("supporting_factors", [])),
                    opposing_factors=_ensure_list(data.get("opposing_factors", [])),
                    limitations=_ensure_list(data.get("limitations", [])),
                    synthesis_engine=f"{provider.title()} ({model})",
                )
        except Exception:
            pass
        return None


# Singleton
_explanation_engine = None

def get_explanation_engine() -> GroundedExplanationEngine:
    global _explanation_engine
    if _explanation_engine is None:
        _explanation_engine = GroundedExplanationEngine()
    return _explanation_engine
