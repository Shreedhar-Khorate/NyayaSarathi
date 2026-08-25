"""
Historical Outcome Analysis and Similarity-Weighted Probability Engine for NyayaSarathi.

Core Functions:
1. User-Position-Aware Outcome Valuation (interpreting court disposals relative to procedural side).
2. Similarity-Weighted Outcome Probability Calculation with Bayesian Prior Smoothing.
3. Transparent Mathematical Telemetry (zero LLM hallucinated probabilities).
"""

from typing import List, Dict, Any, Tuple
import math

from models.prediction import (
    StructuredCaseProfile,
    RankedPrecedent,
    PrecedentOutcomeValuation,
    HistoricalOutcomeDistribution,
    ProbabilityFormulaMetrics,
    Stage3OutcomeResponse,
)


class HistoricalOutcomeAnalyzer:
    """
    Computes data-driven outcome probability based on historical precedents
    and user position.
    """

    # ── RAW OUTCOME CONSTANTS ───────────────────────────────────────────
    FAVORABLE_PETITIONER = {"allowed", "bail_granted", "quashed", "acquitted", "decreed", "granted"}
    UNFAVORABLE_PETITIONER = {"dismissed", "bail_rejected", "convicted", "rejected", "abated"}
    PARTIAL_PETITIONER = {"partly_allowed", "partly_granted", "partially_allowed"}
    NEUTRAL_OUTCOMES = {"disposed", "closed", "ordered", "transferred", "remanded", "other"}

    def map_outcome_for_position(
        self,
        raw_disposal: str,
        user_position: str,
        case_type: str,
    ) -> Tuple[float, str]:
        """
        Maps a court disposal nature to a normalized score [0.0 - 1.0] and label
        from the perspective of the user's procedural position.
        """
        norm_outcome = (raw_disposal or "").strip().lower().replace(" ", "_")
        pos = (user_position or "petitioner").strip().lower()

        # 1. Perspective: Applicant / Petitioner / Appellant / Plaintiff / Complainant
        if pos in ["petitioner", "applicant", "appellant", "plaintiff", "complainant", "unknown"]:
            if norm_outcome in self.FAVORABLE_PETITIONER:
                return 1.0, "Favorable"
            elif norm_outcome in self.UNFAVORABLE_PETITIONER:
                return 0.0, "Unfavorable"
            elif norm_outcome in self.PARTIAL_PETITIONER:
                return 0.60, "Partially Favorable"
            elif norm_outcome == "withdrawn":
                return 0.25, "Unfavorable"
            else:
                return 0.50, "Neutral"

        # 2. Perspective: Respondent / Defendant / Accused (Opposing Side)
        elif pos in ["respondent", "defendant", "accused"]:
            if norm_outcome in self.UNFAVORABLE_PETITIONER:
                # E.g. Appeal dismissed -> Favorable for Respondent
                return 1.0, "Favorable"
            elif norm_outcome in self.FAVORABLE_PETITIONER:
                # E.g. Appeal allowed -> Unfavorable for Respondent
                return 0.0, "Unfavorable"
            elif norm_outcome in self.PARTIAL_PETITIONER:
                return 0.40, "Partially Unfavorable"
            elif norm_outcome == "withdrawn":
                return 0.80, "Favorable"
            else:
                return 0.50, "Neutral"

        return 0.50, "Neutral"

    def analyze_outcomes_and_predict(
        self,
        structured_case: StructuredCaseProfile,
        ranked_precedents: List[RankedPrecedent],
        prior_smoothing_alpha: float = 0.15,
        prior_baseline_prob: float = 50.0,
    ) -> Stage3OutcomeResponse:
        """
        Calculates similarity-weighted outcome probability with Bayesian prior smoothing.
        """
        user_pos = structured_case.user_position
        case_type = structured_case.case_type

        valuations: List[PrecedentOutcomeValuation] = []
        fav_count = 0
        unfav_count = 0
        part_count = 0
        neut_count = 0

        sum_weights = 0.0
        sum_weighted_scores = 0.0

        for prec in ranked_precedents:
            fav_score, outcome_label = self.map_outcome_for_position(
                raw_disposal=prec.outcome,
                user_position=user_pos,
                case_type=case_type,
            )

            # Weight = similarity squared (quadratic emphasis on top matching cases)
            sim = max(0.05, min(0.99, prec.similarity))
            weight = round(sim ** 2, 4)
            weighted_contrib = round(weight * fav_score, 4)

            sum_weights += weight
            sum_weighted_scores += weighted_contrib

            # Update distribution counts
            if outcome_label == "Favorable":
                fav_count += 1
            elif outcome_label == "Unfavorable":
                unfav_count += 1
            elif "Partially" in outcome_label:
                part_count += 1
            else:
                neut_count += 1

            valuations.append(
                PrecedentOutcomeValuation(
                    cnr=prec.cnr,
                    case_name=prec.case_name,
                    court=prec.court,
                    year=prec.year,
                    raw_outcome=prec.outcome,
                    user_position=user_pos,
                    favorable_score=fav_score,
                    outcome_label=outcome_label,
                    similarity=prec.similarity,
                    weight=weight,
                    weighted_contribution=weighted_contrib,
                )
            )

        # ── Data-Driven Probability Formula ─────────────────────────────────
        # P(Favorable) = (Sum(weight_i * score_i) + alpha * P0) / (Sum(weight_i) + alpha)
        p0_ratio = prior_baseline_prob / 100.0  # 0.50
        numerator = sum_weighted_scores + (prior_smoothing_alpha * p0_ratio)
        denominator = sum_weights + prior_smoothing_alpha

        raw_prob = (numerator / denominator) * 100.0

        # Calibration & Bounding: enforce [5.0% - 95.0%]
        calibrated_prob = max(5.0, min(95.0, raw_prob))
        final_integer_prob = int(round(calibrated_prob))

        # Outcome distribution summary
        total_p = len(ranked_precedents)
        unweighted_rate = (
            round((fav_count + (0.5 * part_count) + (0.5 * neut_count)) / total_p * 100.0, 1)
            if total_p > 0
            else 50.0
        )

        dist = HistoricalOutcomeDistribution(
            total_precedents=total_p,
            favorable_count=fav_count,
            unfavorable_count=unfav_count,
            partially_favorable_count=part_count,
            neutral_count=neut_count,
            unweighted_favorable_rate_pct=unweighted_rate,
        )

        formula_str = (
            f"P(Favorable) = [({round(sum_weighted_scores, 4)} + {prior_smoothing_alpha} * 0.50) / "
            f"({round(sum_weights, 4)} + {prior_smoothing_alpha})] * 100 = {round(raw_prob, 2)}%"
        )

        metrics = ProbabilityFormulaMetrics(
            sum_of_weights=round(sum_weights, 4),
            sum_of_weighted_scores=round(sum_weighted_scores, 4),
            prior_smoothing_alpha=prior_smoothing_alpha,
            prior_baseline=prior_baseline_prob,
            raw_calculated_probability_pct=round(raw_prob, 2),
            calibrated_probability_pct=round(calibrated_prob, 2),
            formula_expression=formula_str,
        )

        # Verdict string
        if final_integer_prob >= 65:
            verdict = "Favorable Outcome Likely"
        elif final_integer_prob <= 35:
            verdict = "Unfavorable Outcome Likely"
        else:
            verdict = "Balanced / Discretionary Case"

        # Confidence rating heuristic based on similarity and count
        avg_sim = (sum(p.similarity for p in ranked_precedents) / total_p) if total_p > 0 else 0.0
        if total_p >= 4 and avg_sim >= 0.40:
            confidence = "High"
        elif total_p >= 2 and avg_sim >= 0.20:
            confidence = "Medium"
        else:
            confidence = "Low"

        return Stage3OutcomeResponse(
            status="success",
            case_type=case_type,
            user_position=user_pos,
            success_probability=final_integer_prob,
            predicted_verdict=verdict,
            confidence_hint=confidence,
            precedent_valuations=valuations,
            outcome_distribution=dist,
            probability_metrics=metrics,
            structured_case=structured_case,
            top_precedents=ranked_precedents,
            message=(
                f"Historical outcome analysis completed across {total_p} precedents. "
                f"Data-driven favorable success probability estimated at {final_integer_prob}% ({verdict})."
            ),
        )


# Singleton
_outcome_analyzer = None

def get_outcome_analyzer() -> HistoricalOutcomeAnalyzer:
    global _outcome_analyzer
    if _outcome_analyzer is None:
        _outcome_analyzer = HistoricalOutcomeAnalyzer()
    return _outcome_analyzer

# Backward compatibility alias
get_historical_outcome_analyzer = get_outcome_analyzer
