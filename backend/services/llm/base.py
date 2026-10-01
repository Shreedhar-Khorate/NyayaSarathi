"""
Base LLM Provider Interface & Data Models for NyayaSarathi.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class LLMAnswerResult(BaseModel):
    answer: str
    citation_ids: List[str]
    insufficient_evidence: bool = False
    provider: str
    model: str
    raw_response: Optional[str] = None


class BaseLLMProvider(ABC):
    """Abstract interface for all LLM providers (Cerebras, Groq, Ollama, etc.)."""

    name: str = "base"

    @abstractmethod
    def is_available(self) -> bool:
        """Returns True if the provider is configured and available."""
        pass

    @abstractmethod
    def generate_grounded_answer(
        self,
        question: str,
        evidence_chunks: List[Dict[str, Any]],
        system_prompt: str,
        user_prompt: str,
        timeout_seconds: float = 25.0,
    ) -> LLMAnswerResult:
        """
        Generates an evidence-grounded answer adhering strictly to the evidence pack.
        """
        pass
