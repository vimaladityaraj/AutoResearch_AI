from __future__ import annotations

import json
from typing import Any

import requests

from backend.core.config import get_settings

SYSTEM_PROMPT = (
    "You are AutoResearch AI, a precise competitive-intelligence analyst. "
    "Use only the provided source excerpts and user-provided context. "
    "Return practical, business-oriented analysis. If evidence is limited, say so clearly."
)


class LLMClient:
    """Small Ollama client for local LLM inference."""

    def __init__(self) -> None:
        self.cfg = get_settings()

    def generate(self, prompt: str) -> str:
        if self.cfg.llm_provider.lower() != "ollama":
            raise ValueError("This project currently supports LLM_PROVIDER=ollama.")

        url = f"{self.cfg.ollama_base_url.rstrip('/')}/api/chat"
        payload: dict[str, Any] = {
            "model": self.cfg.ollama_model,
            "stream": False,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "options": {
                "temperature": 0.2,
                "num_ctx": 8192,
            },
        }

        response = requests.post(url, json=payload, timeout=180)
        response.raise_for_status()

        data = response.json()
        return data.get("message", {}).get("content", "").strip()

    def generate_json(self, prompt: str) -> dict:
        """Ask the local model for JSON and defensively parse the response."""
        json_prompt = (
            prompt
            + "\n\nReturn ONLY valid JSON. Do not include markdown fences, explanations, or prose outside the JSON object."
        )
        raw = self.generate(json_prompt)

        # Handle models that wrap JSON inside markdown fences or extra text.
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1 and end > start:
            raw = raw[start : end + 1]

        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed
            return {"raw_response": str(parsed)}
        except Exception:
            return {"raw_response": raw}
