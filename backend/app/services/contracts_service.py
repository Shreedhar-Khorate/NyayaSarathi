"""
Contract Red-Flag Analyzer — Sample Implementation
TODO: Replace with NLP/LLM-based clause risk detection.
"""
from app.schemas.contracts import ContractAnalysisResponse, RedFlag


def analyze_contract(filename: str) -> ContractAnalysisResponse:
    # Sample static analysis — replace with actual document parsing
    return ContractAnalysisResponse(
        red_flags=[
            RedFlag(
                clause_text="The vendor shall not be liable for any indirect or consequential damages howsoever arising.",
                risk_level="high",
                explanation=(
                    "This blanket exclusion of consequential damages can prevent recovery of lost profits, "
                    "which are often the primary loss in a breach-of-contract scenario."
                ),
                page_ref=3,
            ),
            RedFlag(
                clause_text="Either party may terminate this agreement with 7 days notice.",
                risk_level="medium",
                explanation=(
                    "A 7-day termination notice is unusually short for a long-term services agreement "
                    "and leaves little time to find an alternative vendor."
                ),
                page_ref=7,
            ),
        ],
        overall_risk_score="Medium-High",
    )
