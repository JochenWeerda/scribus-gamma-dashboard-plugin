import json
from pathlib import Path

from packages.dialog_engine import DecisionStore


def test_decision_store_migrates_flat_json_on_save(tmp_path: Path):
    p = tmp_path / "decisions.json"
    p.write_text(json.dumps({"format": "A4"}, indent=2), encoding="utf-8")

    store = DecisionStore(p)
    assert store.load()["format"] == "A4"

    store.set("variants", "both", source="test")
    raw = store.load_raw()
    assert "decisions" in raw
    assert raw["decisions"]["format"] == "A4"
    assert raw["decisions"]["variants"] == "both"
    assert "meta" in raw

