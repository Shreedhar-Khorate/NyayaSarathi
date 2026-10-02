"""
Groq LLM Provider for NyayaSarathi.
High-throughput fallback inference provider.
"""

import os
import re
import logging
from typing import List, Dict, Any, Optional

from services.llm.base import BaseLLMProvider, LLMAnswerResult

logger = logging.getLogger("nyayasarathi.llm.groq")


class GroqProvider(BaseLLMProvider):
    name: str = "groq"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self._api_key = api_key
        self.model = model or os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile").strip()

    @property
    def api_key(self) -> str:
        return (self._api_key or os.environ.get("GROQ_API_KEY", "")).strip()

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
            raise ValueError("Groq API key is not configured.")

        preferred_model = os.environ.get("GROQ_MODEL", self.model).strip()
        candidate_models = [
            preferred_model,
            "openai/gpt-oss-120b",
            "openai/gpt-oss-20b",
            "qwen/qwen3.8-27b",
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
        ]
        # De-duplicate while preserving order
        unique_models = []
        for m in candidate_models:
            if m and m not in unique_models:
                unique_models.append(m)

        last_err = None

        # Try using groq Python SDK
        try:
            from groq import Groq
            client = Groq(api_key=active_key)
            for m in unique_models:
                try:
                    response = client.chat.completions.create(
                        model=m,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        temperature=0.1,
                        max_tokens=1000,
                    )
                    raw_content = response.choices[0].message.content or ""
                    return self._parse_response(raw_content, m)
                except Exception as ex:
                    last_err = ex
                    logger.warning(f"Groq model {m} failed: {ex}. Trying next candidate...")
                    continue
            if last_err:
                raise last_err
        except ImportError:
            import httpx
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            for m in unique_models:
                try:
                    payload = {
                        "model": m,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        "temperature": 0.1,
                        "max_tokens": 1000,
                    }
                    with httpx.Client(timeout=timeout_seconds) as client:
                        res = client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                        res.raise_for_status()
                        data = res.json()
                        raw_content = data["choices"][0]["message"]["content"]
                        return self._parse_response(raw_content, m)
                except Exception as ex:
                    last_err = ex
                    continue
            if last_err:
                raise last_err

        raise ValueError("No viable Groq model succeeded.")

    def _parse_response(self, raw_content: str, used_model: str) -> LLMAnswerResult:
        # Normalize full-width/unicode brackets like 【S1】 -> [S1]
        normalized_content = raw_content.replace("【", "[").replace("】", "]")
        citations = list(set(re.findall(r"\[(S\d+)\]", normalized_content, re.IGNORECASE)))
        citations = [c.upper() for c in citations]
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
            provider="groq",
            model=used_model,
            raw_response=raw_content,
        )
