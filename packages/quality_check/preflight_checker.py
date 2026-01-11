from __future__ import annotations

from typing import Any, Dict, List

from .layout_validator import validate_layout_semantics


def run_preflight(layout_json: Dict[str, Any], *, checks: List[str] | None = None) -> tuple[bool, List[str]]:
    """
    MVP preflight:
    - schema + semantic validation
    """

    return validate_layout_semantics(layout_json, checks=checks)
