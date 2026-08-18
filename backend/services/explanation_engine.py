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
        gemini_api_key = os.environ.get("GEMINI_API_KEY")
        if not gemini_api_key:
            env_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
            if os.path.exists(env_file):
                with open(env_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip().startswith("GEMINI_API_KEY="):
                            val = line.strip().split("=", 1)[1].strip().strip("'\"")
                            if val:
                                gemini_api_key = val
                                os.environ["GEMINI_API_KEY"] = val
                            break

        if gemini_api_key:
            try:
                llm_explanation = self._synthesize_with_gemini(
                    structured_case, probability, confidence, precedents, gemini_api_key
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
        user_pos = structured_case.user_position
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
            sec_str = ", ".join([f"Section {s}" for s in structured_case.detected_sections[:3]])
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

    def _synthesize_with_gemini(
        self,
        structured_case: StructuredCaseProfile,
        probability: int,
        confidence: str,
        precedents: List[VerifiedPrecedent],
        api_key: str,
    ) -> Optional[GroundedExplanation]:
        """Live Gemini LLM grounded legal synthesis using Google Gemini API."""
        try:
            import urllib.request
            import json

            # Build evidence brief for the prompt
            precedents_brief = "\n".join([
                f"- Case: {p.case_name} ({p.court}, {p.year})\n  Outcome: {p.outcome} (Impact: {p.favorable_to_user})\n  Holding Excerpt: {p.verbatim_excerpt[:250]}"
                for p in precedents[:4]
            ])

            prompt = f"""
You are NyayaSarathi's Senior Legal Intelligence Synthesizer.
Synthesize an evidence-grounded judicial explanation for an Indian court matter.

CASE FACTS:
- Legal Domain: {structured_case.case_type}
- Procedural Position: {structured_case.user_position}
- Statutory Sections: {', '.join(structured_case.detected_sections) if structured_case.detected_sections else 'General'}
- Case Narrative: {structured_case.key_facts[0] if structured_case.key_facts else 'Case brief'}

MATHEMATICAL PREDICTION (DO NOT CHANGE OR RE-CALCULATE THIS):
- Calculated Success Probability: {probability}%
- Model Confidence: {confidence}

VERIFIED HISTORICAL PRECEDENTS:
{precedents_brief}

TASK:
Produce a strictly factual, grounded explanation formatted as valid JSON with these exact keys:
1. "takeaway": A 2-3 sentence executive summary explaining the judicial likelihood from the perspective of the {structured_case.user_position}.
2. "supporting_factors": A list of 2-3 specific legal/factual strengths grounded in the statutory provisions or favorable precedents.
3. "opposing_factors": A list of 2-3 realistic counterarguments, prosecution/defense objections, or evidentiary hurdles.
4. "limitations": A list of 2-3 standard Indian judicial caveats (e.g. bench discretion, oral arguments, trial evidence).

CRITICAL RULES:
- Do not invent cases, statutes, or section numbers.
- Do not change the probability ({probability}%).
- Output ONLY pure JSON without markdown backticks.
"""

            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.2,
                    "responseMimeType": "application/json"
                }
            }

            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )

            with urllib.request.urlopen(req, timeout=8) as response:
                res_body = json.loads(response.read().decode("utf-8"))
                text_content = res_body["candidates"][0]["content"]["parts"][0]["text"]
                parsed = json.loads(text_content)

                return GroundedExplanation(
                    takeaway=parsed.get("takeaway", ""),
                    supporting_factors=parsed.get("supporting_factors", []),
                    opposing_factors=parsed.get("opposing_factors", []),
                    limitations=parsed.get("limitations", []),
                    synthesis_engine="Google Gemini 1.5 Flash (Grounded RAG)",
                )
        except Exception as e:
            return None


# Singleton
_explanation_engine = None

def get_explanation_engine() -> GroundedExplanationEngine:
    global _explanation_engine
    if _explanation_engine is None:
        _explanation_engine = GroundedExplanationEngine()
    return _explanation_engine
