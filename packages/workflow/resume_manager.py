from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Tuple


@dataclass
class ResumeManager:
    path: Path

    SCHEMA_VERSION = "1.0"

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def load_raw(self) -> Dict[str, Any]:
        if not self.path.exists():
            return {}
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}

    def load(self) -> Dict[str, Any]:
        """
        Load normalized workflow state (schema_versioned).
        Migrates legacy flat state shapes.
        """
        raw = self.load_raw()
        if not raw:
            return {
                "schema_version": self.SCHEMA_VERSION,
                "meta": {"created_at": self._now(), "updated_at": self._now()},
                "steps": {},
            }

        if raw.get("schema_version") == self.SCHEMA_VERSION and isinstance(raw.get("steps"), dict):
            raw.setdefault("meta", {})
            raw["meta"].setdefault("created_at", self._now())
            raw["meta"]["updated_at"] = self._now()
            return raw

        # Legacy migration: previously we stored keys like {"converted": {...}, "variants": {...}}
        state = {
            "schema_version": self.SCHEMA_VERSION,
            "meta": {"created_at": self._now(), "updated_at": self._now()},
            "steps": {},
            "legacy": raw,
        }

        steps = state["steps"]
        if "converted" in raw:
            steps["convert_manifest"] = {
                "status": "completed",
                "completed_at": self._now(),
                "outputs": raw.get("converted", {}).get("outputs", []),
                "summary": {"valid": raw.get("converted", {}).get("valid")},
                "input_hash": None,
            }
        if "variants" in raw:
            steps["generate_variants"] = {
                "status": "completed",
                "completed_at": self._now(),
                "outputs": (raw.get("variants", {}) or {}).get("outputs", []),
                "summary": {"errors": (raw.get("variants", {}) or {}).get("errors")},
                "input_hash": None,
            }

        return state

    def save(self, state: Dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        state = dict(state)
        state.setdefault("schema_version", self.SCHEMA_VERSION)
        state.setdefault("meta", {})
        state["meta"].setdefault("created_at", self._now())
        state["meta"]["updated_at"] = self._now()
        self.path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    def get_step(self, state: Dict[str, Any], step_id: str) -> Dict[str, Any]:
        state.setdefault("steps", {})
        steps = state["steps"]
        step = steps.get(step_id)
        if not isinstance(step, dict):
            step = {"status": "pending"}
            steps[step_id] = step
        return step

    def mark_step_running(self, state: Dict[str, Any], step_id: str, *, input_hash: str) -> None:
        step = self.get_step(state, step_id)
        step.update({"status": "running", "started_at": self._now(), "input_hash": input_hash, "error": None})

    def mark_step_completed(self, state: Dict[str, Any], step_id: str, *, outputs: Any = None, summary: Any = None) -> None:
        step = self.get_step(state, step_id)
        step.update({"status": "completed", "completed_at": self._now()})
        if outputs is not None:
            step["outputs"] = outputs
        if summary is not None:
            step["summary"] = summary

    def mark_step_failed(self, state: Dict[str, Any], step_id: str, *, error: str) -> None:
        step = self.get_step(state, step_id)
        step.update({"status": "failed", "completed_at": self._now(), "error": error})


def _hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_file(path: Path) -> str:
    """
    Hash file contents. Uses full content for <= 2MB, otherwise hashes head+tail+size.
    """
    b = path.read_bytes()
    if len(b) <= 2_000_000:
        return _hash_bytes(b)
    head = b[:65536]
    tail = b[-65536:]
    return _hash_bytes(head + tail + str(len(b)).encode("utf-8"))


def hash_inputs(obj: Any) -> str:
    """
    Deterministic hash for step inputs (JSON-serializable).
    """
    encoded = json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return _hash_bytes(encoded)
