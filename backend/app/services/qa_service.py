"""
RAG Q&A Service — Sample Implementation
TODO: Replace with Llama 3 / Mistral local inference + Qdrant retrieval.
"""
from app.schemas.qa import QARequest, QAResponse, Citation


def answer_question(request: QARequest) -> QAResponse:
    # Sample grounded answer — replace with actual RAG pipeline
    return QAResponse(
        answer=(
            "Based on the retrieved case documents, a Section 65B certificate is a mandatory "
            "requirement for admissibility of electronic evidence. The Supreme Court in "
            "Arjun Panditrao Khotkar (2020) clarified that the certificate must accompany "
            "the electronic record at the time of tendering evidence."
        ),
        citations=[
            Citation(
                document="Arjun Panditrao Khotkar vs. Kailash Kushanrao Gorantyal",
                page=12,
                excerpt=(
                    "We hold that a certificate under Section 65B(4) is a condition precedent "
                    "to the admissibility of electronic evidence."
                ),
            ),
            Citation(
                document="Anvar P.V. vs. P.K. Basheer (2014)",
                page=8,
                excerpt=(
                    "Any electronic document produced without the Section 65B certificate "
                    "is inadmissible in evidence."
                ),
            ),
        ],
    )
