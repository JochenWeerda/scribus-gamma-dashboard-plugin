from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .decision_store import DecisionStore
from .question_engine import Question, build_default_questionnaire, unresolved_questions, validate_decisions


@dataclass
class DialogSession:
    store: DecisionStore
    questions: List[Question] = None  # type: ignore[assignment]
    decisions: Dict[str, Any] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.questions is None:
            self.questions = build_default_questionnaire()
        if self.decisions is None:
            self.decisions = self.store.load()

    def next_question(self) -> Optional[Question]:
        remaining = unresolved_questions(self.questions, self.decisions)
        if not remaining:
            return None
        return remaining[0]

    def answer(self, key: str, value: Any, *, source: str = "cli") -> None:
        self.decisions[key] = value
        ok, errors = validate_decisions(self.questions, self.decisions, require_all=False)
        if not ok:
            # rollback the last answer for interactive sessions
            self.decisions.pop(key, None)
            raise ValueError("; ".join(errors[:5]))
        self.store.save(self.decisions, source=source)

    def is_complete(self) -> bool:
        return self.next_question() is None
