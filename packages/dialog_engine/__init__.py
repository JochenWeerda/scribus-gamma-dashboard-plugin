"""Dialog Engine (MVP).

Provides:
- a small question catalog derived from design decisions
- decision persistence to JSON (project config)
- optional hooks to RAG and an LLM layer (kept lazy to avoid heavy deps)
"""

from .question_engine import Choice, Question, build_default_questionnaire
from .decision_store import DecisionStore
from .session import DialogSession
from .agents import AgentExecutor, AgentPrompt, AGENT_REGISTRY

__all__ = [
    "Choice",
    "Question",
    "DecisionStore",
    "DialogSession",
    "build_default_questionnaire",
    "AgentExecutor",
    "AgentPrompt",
    "AGENT_REGISTRY",
]
