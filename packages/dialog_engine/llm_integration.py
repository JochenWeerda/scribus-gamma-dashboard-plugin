from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


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

