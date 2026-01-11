from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional


SCHEMA_VERSION = "1.0"


@dataclass(frozen=True)
class Choice:
    value: str
    label: str
    description: str | None = None


@dataclass(frozen=True)
class Question:
    key: str
    prompt: str
    kind: str = "choice"  # choice|text|number|bool
    choices: List[Choice] | None = None
    default: Any = None
    required: bool = True
    help: str | None = None
    block: str = "core"
    depends_on: Dict[str, Any] | None = None


def build_default_questionnaire() -> List[Question]:
    """
    MVP question catalog. This intentionally mirrors `.cursor/MAGAZIN_WORKFLOW_DESIGN_DECISIONS.md`.
    The result is stable and can be used by a CLI or a future plugin UI.
    """

    return [
        Question(
            key="format",
            prompt="Welches Seitenformat?",
            block="format",
            choices=[
                Choice("A4", "DIN A4 (210x297mm)"),
                Choice("8x11.5", "8x11,5 Zoll (Amazon)"),
                Choice("both", "Beide Varianten (A4 + 8x11,5)"),
            ],
            default="A4",
        ),
        Question(
            key="variants",
            prompt="Welche Output-Varianten?",
            block="format",
            choices=[
                Choice("color", "Farbig (mit Bleed)"),
                Choice("grayscale", "Schwarz/Weiss/Graustufen (KDP)"),
                Choice("both", "Beides"),
            ],
            default="both",
        ),
        Question(
            key="akt_colors",
            prompt="Akt-Farben verwenden?",
            block="acts",
            choices=[
                Choice("standard", "Standardfarben (laut Designentscheidungen)"),
                Choice("auto", "Auto-Sampling aus Hero-Bildern"),
                Choice("custom", "Custom (manuell)"),
            ],
            default="standard",
        ),
        Question(
            key="layout_density",
            prompt="Layout-Dichte?",
            block="layout",
            choices=[
                Choice("compact", "Kompakt (mehr Content, weniger Weissraum)"),
                Choice("standard", "Standard"),
                Choice("spacious", "Luftig (mehr Weissraum)"),
            ],
            default="standard",
        ),
        Question(
            key="sidebar_detection",
            prompt="Sidebar-Erkennung?",
            block="layout",
            choices=[
                Choice("auto", "Auto (Tags, sonst Heuristiken)"),
                Choice("tags_only", "Nur Tags"),
                Choice("heuristics_only", "Nur Heuristiken"),
            ],
            default="auto",
        ),
        Question(
            key="infographic_handling",
            prompt="Infografiken-Handling?",
            block="layout",
            choices=[
                Choice("standard", "Standard"),
                Choice("compact", "Kompakt (aggressiver Merge)"),
                Choice("conservative", "Konservativ (weniger Merge)"),
            ],
            default="standard",
        ),
    ]


def iter_applicable_questions(questions: Iterable[Question], decisions: Dict[str, Any]) -> Iterable[Question]:
    """
    Yield only questions whose `depends_on` conditions are satisfied.
    Condition format: { "key": "expected_value" }.
    """
    for q in questions:
        if not q.depends_on:
            yield q
            continue
        ok = True
        for dep_key, dep_val in q.depends_on.items():
            if decisions.get(dep_key) != dep_val:
                ok = False
                break
        if ok:
            yield q


def unresolved_questions(questions: Iterable[Question], decisions: Dict[str, Any]) -> List[Question]:
    """Return the remaining questions not answered in `decisions`."""
    remaining: List[Question] = []
    for q in iter_applicable_questions(questions, decisions):
        if q.required and q.key not in decisions:
            remaining.append(q)
    return remaining


def validate_decisions(
    questions: Iterable[Question],
    decisions: Dict[str, Any],
    *,
    require_all: bool = True,
) -> tuple[bool, list[str]]:
    errors: list[str] = []
    qmap = {q.key: q for q in questions}

    for key, q in qmap.items():
        if q.depends_on:
            # Skip validation of non-applicable questions.
            applicable = True
            for dep_key, dep_val in q.depends_on.items():
                if decisions.get(dep_key) != dep_val:
                    applicable = False
                    break
            if not applicable:
                continue

        if require_all and q.required and key not in decisions:
            errors.append(f"Missing required decision: {key}")
            continue

        if key not in decisions:
            continue

        value = decisions[key]
        if q.kind == "choice" and q.choices:
            allowed = {c.value for c in q.choices}
            if value not in allowed:
                errors.append(f"Invalid value for {key}: {value!r}. Allowed: {sorted(allowed)}")

    return (len(errors) == 0), errors
