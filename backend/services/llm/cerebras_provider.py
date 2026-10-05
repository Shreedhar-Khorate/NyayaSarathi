"""
Cerebras Cloud SDK / REST LLM Provider for NyayaSarathi.
Ultra-fast inference provider configured as primary LLM.
"""

import os
import re
import json
import logging
from typing import List, Dict, Any, Optional

from services.llm.base import BaseLLMProvider, LLMAnswerResult

logger = logging.getLogger("nyayasarathi.llm.cerebras")


class CerebrasProvider(BaseLLMProvider):
    name: str = "cerebras"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self._api_key = api_key
        self.model = model or os.environ.get("CEREBRAS_MODEL", "llama3.1-8b").strip()

    @property
    def api_key(self) -> str:
        return (self._api_key or os.environ.get("CEREBRAS_API_KEY", "")).strip()

    def is_available(self) -> bool:
        return bool(self.api_key)

    def generate_grounded_answer(
        self,
        question: str,
        evidence_chunks: List[Dict[str, Any]],
        system_prompt: str,
        user_prompt: str,
        timeout_seconds: float = 25.0,
    ) -> LLMAnswerResult:
        active_key = self.api_key
        if not active_key:
            raise ValueError("Cerebras API key is not configured.")

        active_model = os.environ.get("CEREBRAS_MODEL", self.model).strip()

        # Try using cerebras-cloud-sdk
        try:
            from cerebras.cloud.sdk import Cerebras
            client = Cerebras(api_key=active_key)
            response = client.chat.completions.create(
                model=active_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                max_tokens=1000,
            )
            raw_content = response.choices[0].message.content or ""
            return self._parse_response(raw_content)
        except ImportError:
            # Fallback to direct HTTPX call
            import httpx
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.1,
                "max_tokens": 1000,
            }
            with httpx.Client(timeout=timeout_seconds) as client:
                res = client.post("https://api.cerebras.ai/v1/chat/completions", headers=headers, json=payload)
                res.raise_for_status()
                data = res.json()
                raw_content = data["choices"][0]["message"]["content"]
                return self._parse_response(raw_content)

    def _parse_response(self, raw_content: str) -> LLMAnswerResult:
        # Extract citation markers [S1], [S2], etc.
        citations = list(set(re.findall(r"\[(S\d+)\]", raw_content)))
        citations.sort(key=lambda x: int(x[1:]) if x[1:].isdigit() else 999)

        # Check for insufficient evidence markers
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
            provider="cerebras",
            model=self.model,
            raw_response=raw_content,
        )
