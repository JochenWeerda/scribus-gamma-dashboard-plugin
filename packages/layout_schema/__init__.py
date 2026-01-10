"""Layout Schema Package - JSON Schema und Validierung für Layout-Definitionen."""

import json
import jsonschema
from pathlib import Path

SCHEMA_PATH = Path(__file__).parent / "layout-mvp.schema.json"


def load_schema():
    """Lädt das JSON Schema."""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_layout(layout_json: dict) -> tuple[bool, list[str]]:
    """
    Validiert ein Layout-JSON gegen das Schema.
    
    Returns:
        (is_valid, errors): Tuple mit Validitäts-Flag und Liste von Fehlermeldungen
    """
    schema = load_schema()
    validator = jsonschema.Draft7Validator(schema)
    errors = [str(e) for e in validator.iter_errors(layout_json)]
    return len(errors) == 0, errors

