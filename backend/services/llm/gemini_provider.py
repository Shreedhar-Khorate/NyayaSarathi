"""
Google Gemini LLM Provider for NyayaSarathi.
High-accuracy grounded inference provider.
"""

import os
import re
import json
import logging
from typing import List, Dict, Any, Optional

from services.llm.base import BaseLLMProvider, LLMAnswerResult

logger = logging.getLogger("nyayasarathi.llm.gemini")


class GeminiProvider(BaseLLMProvider):
    name: str = "gemini"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self._api_key = api_key
        self.model = model or os.environ.get("GEMINI_MODEL", "gemini-1.5-flash").strip()

    @property
    def api_key(self) -> str:
        key = (self._api_key or os.environ.get("GEMINI_API_KEY", "")).strip()
        if not key:
            env_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
            if os.path.exists(env_file):
                try:
                    with open(env_file, "r", encoding="utf-8") as f:
                        for line in f:
                            if line.strip().startswith("GEMINI_API_KEY="):
                                val = line.strip().split("=", 1)[1].strip().strip("'\"")
                                if val:
                                    key = val
                                    os.environ["GEMINI_API_KEY"] = val
                                break
                except Exception:
                    pass
        return key

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
            raise ValueError("Gemini API key is not configured.")

        active_model = os.environ.get("GEMINI_MODEL", self.model).strip()

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{active_model}:generateContent?key={active_key}"
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": f"{system_prompt}\n\n{user_prompt}"
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 1200,
            }
        }

        try:
            import httpx
            with httpx.Client(timeout=timeout_seconds) as client:
                res = client.post(url, json=payload, headers={"Content-Type": "application/json"})
                res.raise_for_status()
                data = res.json()
        except ImportError:
            import urllib.request
            req_data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=req_data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=timeout_seconds) as response:
                data = json.loads(response.read().decode("utf-8"))

        candidates = data.get("candidates", [])
        if not candidates:
            raise ValueError("Gemini returned empty candidate response.")

        parts = candidates[0].get("content", {}).get("parts", [])
        raw_content = parts[0].get("text", "") if parts else ""

        return self._parse_response(raw_content, active_model)

    def _parse_response(self, raw_content: str, model_name: str) -> LLMAnswerResult:
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
            provider="gemini",
            model=model_name,
            raw_response=raw_content,
        )
