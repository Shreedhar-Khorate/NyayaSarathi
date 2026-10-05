"""
Ollama Local LLM Provider for NyayaSarathi.
Optional self-hosted local model provider for development/offline deployment.
"""

import os
import re
import logging
from typing import List, Dict, Any, Optional

from services.llm.base import BaseLLMProvider, LLMAnswerResult

logger = logging.getLogger("nyayasarathi.llm.ollama")


class OllamaProvider(BaseLLMProvider):
    name: str = "ollama"

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.base_url = (base_url or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
        self.model = model or os.environ.get("OLLAMA_MODEL", "llama3.2").strip()

    def is_available(self) -> bool:
        # Check if Ollama service is reachable
        try:
            import httpx
            with httpx.Client(timeout=2.0) as client:
                res = client.get(f"{self.base_url}/api/tags")
                return res.status_code == 200
        except Exception:
            return False

    def generate_grounded_answer(
        self,
        question: str,
        evidence_chunks: List[Dict[str, Any]],
        system_prompt: str,
        user_prompt: str,
        timeout_seconds: float = 35.0,
    ) -> LLMAnswerResult:
        import httpx
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "options": {
                "temperature": 0.1,
            },
        }
        with httpx.Client(timeout=timeout_seconds) as client:
            res = client.post(f"{self.base_url}/api/chat", json=payload)
            res.raise_for_status()
            data = res.json()
            raw_content = data.get("message", {}).get("content", "")

        citations = list(set(re.findall(r"\[(S\d+)\]", raw_content)))
        citations.sort(key=lambda x: int(x[1:]) if x[1:].isdigit() else 999)

        insufficient = False
        lower = raw_content.lower()
        if (
            "insufficient evidence" in lower
            or "does not contain" in lower
            or "cannot be determined from the provided" in lower
            or "no relevant information" in lower
        ):
            insufficient = True

        return LLMAnswerResult(
            answer=raw_content.strip(),
            citation_ids=citations,
            insufficient_evidence=insufficient,
            provider="ollama",
            model=self.model,
            raw_response=raw_content,
        )
