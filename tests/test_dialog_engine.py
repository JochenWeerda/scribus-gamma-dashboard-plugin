from pathlib import Path

from packages.dialog_engine import DecisionStore, build_default_questionnaire
from packages.dialog_engine.question_engine import validate_decisions


def test_decision_store_roundtrip(tmp_path: Path):
    p = tmp_path / "decisions.json"
    store = DecisionStore(p)
    store.set("format", "A4", source="test")
    assert store.get("format") == "A4"


def test_default_questionnaire_validation():
    qs = build_default_questionnaire()
    ok, errors = validate_decisions(qs, {"format": "A4", "variants": "both"})
    assert not ok
    assert any("Missing required decision" in e for e in errors)
