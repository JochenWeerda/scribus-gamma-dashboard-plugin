from __future__ import annotations

from typing import Any, Dict, List

from packages.variant_generator.amazon_validator import validate_kdp_layout


def check_amazon_constraints(layout_json: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    MVP Amazon checker:
    - delegates to variant_generator.validate_kdp_layout
    """

    return validate_kdp_layout(layout_json)

