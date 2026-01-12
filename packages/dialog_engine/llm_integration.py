from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import os


@dataclass(frozen=True)
class LLMRequest:
    system: str
    user: str


class LLMClient:
    """
    Minimal interface. Implementation is intentionally left out to avoid coupling
    to a specific provider and to keep tests offline by default.
    """

    def complete(self, request: LLMRequest) -> str:  # pragma: no cover
        raise NotImplementedError


class DisabledLLM(LLMClient):
    def complete(self, request: LLMRequest) -> str:  # pragma: no cover
        raise RuntimeError("LLM is disabled (no provider configured)")


class OpenAILLM(LLMClient):
    def __init__(self, api_key: str, model: str, base_url: Optional[str] = None, timeout: float = 30.0):
        try:
            from openai import OpenAI
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("OpenAI client not installed. Install with: pip install openai") from exc

        self._client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)
        self._model = model

    def complete(self, request: LLMRequest) -> str:  # pragma: no cover
        resp = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": request.system},
                {"role": "user", "content": request.user},
            ],
        )
        return resp.choices[0].message.content or ""


def build_llm_from_env() -> LLMClient:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return DisabledLLM()

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    base_url = os.getenv("OPENAI_BASE_URL")
    timeout = float(os.getenv("OPENAI_TIMEOUT", "30"))
    return OpenAILLM(api_key=api_key, model=model, base_url=base_url, timeout=timeout)

