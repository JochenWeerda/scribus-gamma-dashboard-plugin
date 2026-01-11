from __future__ import annotations

import json
from datetime import datetime, timezone
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from .question_engine import SCHEMA_VERSION


@dataclass
class DecisionStore:
    """
    Persist decisions to a JSON file.

    This is intentionally simple (no DB) and acts as a building block for the workflow orchestrator.
    """

    path: Path

    def load_raw(self) -> Dict[str, Any]:
        if not self.path.exists():
            return {}
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
        return {}

    def load(self) -> Dict[str, Any]:
        """
        Load only the `decisions` dict.
        Supports legacy flat JSON (migration-on-read).
        """
        raw = self.load_raw()
        if not raw:
            return {}
        if "decisions" in raw and isinstance(raw.get("decisions"), dict):
            return dict(raw["decisions"])
        # Legacy flat dict
        return dict(raw)

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _wrap(self, decisions: Dict[str, Any], *, previous: Optional[Dict[str, Any]] = None, source: str = "unknown") -> Dict[str, Any]:
        prev = previous or {}
        meta = prev.get("meta") if isinstance(prev.get("meta"), dict) else {}
        created_at = meta.get("created_at") or self._now()
        history = prev.get("history") if isinstance(prev.get("history"), list) else []

        doc = {
            "schema_version": SCHEMA_VERSION,
            "decisions": decisions,
            "meta": {
                "created_at": created_at,
                "updated_at": self._now(),
            },
            "history": history,
        }

        # Add history entry if this is an update and not a brand new file.
        if prev:
            doc["history"] = [
                *history,
                {"ts": self._now(), "source": source, "keys": sorted(list(decisions.keys()))},
            ]
        return doc

    def save(self, data: Dict[str, Any], *, source: str = "unknown") -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        prev = self.load_raw()
        doc = self._wrap(dict(data), previous=prev, source=source)
        self.path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")

    def get(self, key: str, default: Any = None) -> Any:
        return self.load().get(key, default)

    def set(self, key: str, value: Any, *, source: str = "unknown") -> None:
        data = self.load()
        data[key] = value
        self.save(data, source=source)

    def merge(self, patch: Dict[str, Any], *, source: str = "unknown") -> Dict[str, Any]:
        data = self.load()
        data.update(patch)
        self.save(data, source=source)
        return data
