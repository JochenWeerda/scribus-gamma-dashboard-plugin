"""Dialog Engine API endpoints (session-based, Redis-backed).

This provides a thin backend wrapper around `packages.dialog_engine` so the plugin/UI
can drive the decision dialog without duplicating logic.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status, Header
from pydantic import BaseModel, Field

from packages.cache import get_cache
from packages.dialog_engine.question_engine import (
    SCHEMA_VERSION,
    build_default_questionnaire,
    unresolved_questions,
    validate_decisions,
)
from packages.event_bus import get_event_bus

from config import config


def verify_api_key(x_api_key: str = Header(None, alias="X-API-Key")):
    """Verifiziert API-Key (wenn aktiviert)."""
    if not config.API_KEY_ENABLED:
        return True
    # We intentionally accept the same header name used elsewhere.
    if not x_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API key")
    if x_api_key != config.API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API key")
    return True

router = APIRouter(prefix="/v1/dialog", tags=["dialog"])


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _cache_key(session_id: str) -> str:
    return f"dialog:{session_id}"


def _question_to_dict(q) -> Dict[str, Any]:
    d = asdict(q)
    # Keep payload stable and minimal
    return {
        "key": d["key"],
        "prompt": d["prompt"],
        "kind": d.get("kind", "choice"),
        "choices": d.get("choices") or [],
        "default": d.get("default"),
        "required": bool(d.get("required", True)),
        "help": d.get("help"),
        "block": d.get("block", "core"),
        "depends_on": d.get("depends_on"),
    }


class CreateSessionRequest(BaseModel):
    session_id: Optional[str] = Field(default=None, description="Optional fixed session id")
    initial_decisions: Dict[str, Any] = Field(default_factory=dict)
    ttl_seconds: int = Field(default=24 * 3600, ge=60, le=7 * 24 * 3600)


class SessionInfo(BaseModel):
    session_id: str
    schema_version: str
    decisions: Dict[str, Any]
    next_question: Optional[Dict[str, Any]] = None
    complete: bool


class AnswerRequest(BaseModel):
    key: str
    value: Any


class ExportProjectInitRequest(BaseModel):
    template: Dict[str, Any] = Field(default_factory=dict, description="Optional project_init template to merge into")


@router.get("/questions")
def list_questions(_: bool = Depends(verify_api_key)) -> Dict[str, Any]:
    questions = build_default_questionnaire()
    return {"schema_version": SCHEMA_VERSION, "questions": [_question_to_dict(q) for q in questions]}


@router.post("/sessions", response_model=SessionInfo, status_code=status.HTTP_201_CREATED)
def create_session(req: CreateSessionRequest, _: bool = Depends(verify_api_key)) -> SessionInfo:
    cache = get_cache()
    event_bus = get_event_bus() if config.EVENT_BUS_ENABLED else None

    session_id = req.session_id or str(uuid4())
    key = _cache_key(session_id)

    decisions = dict(req.initial_decisions or {})
    ok, errors = validate_decisions(build_default_questionnaire(), decisions, require_all=False)
    if not ok:
        raise HTTPException(status_code=400, detail={"validation_errors": errors})

    payload = {
        "schema_version": SCHEMA_VERSION,
        "decisions": decisions,
        "created_at": _now(),
        "updated_at": _now(),
        "ttl_seconds": int(req.ttl_seconds),
    }
    cache.set(key, payload, ttl=req.ttl_seconds)

    if event_bus is not None and getattr(event_bus, "enabled", False):
        event_bus.publish("dialog", "dialog.session.created", {"session_id": session_id, "schema_version": SCHEMA_VERSION})

    questions = build_default_questionnaire()
    nxt = unresolved_questions(questions, decisions)
    next_q = _question_to_dict(nxt[0]) if nxt else None
    return SessionInfo(
        session_id=session_id,
        schema_version=SCHEMA_VERSION,
        decisions=decisions,
        next_question=next_q,
        complete=next_q is None,
    )


@router.get("/sessions/{session_id}", response_model=SessionInfo)
def get_session(session_id: str, _: bool = Depends(verify_api_key)) -> SessionInfo:
    cache = get_cache()
    payload = cache.get(_cache_key(session_id))
    if not payload:
        raise HTTPException(status_code=404, detail="Dialog session not found")
    decisions = payload.get("decisions") or {}
    questions = build_default_questionnaire()
    nxt = unresolved_questions(questions, decisions)
    next_q = _question_to_dict(nxt[0]) if nxt else None
    return SessionInfo(
        session_id=session_id,
        schema_version=payload.get("schema_version") or SCHEMA_VERSION,
        decisions=decisions,
        next_question=next_q,
        complete=next_q is None,
    )


@router.post("/sessions/{session_id}/answer", response_model=SessionInfo)
def answer(session_id: str, req: AnswerRequest, _: bool = Depends(verify_api_key)) -> SessionInfo:
    cache = get_cache()
    event_bus = get_event_bus() if config.EVENT_BUS_ENABLED else None

    key = _cache_key(session_id)
    payload = cache.get(key)
    if not payload:
        raise HTTPException(status_code=404, detail="Dialog session not found")

    decisions = payload.get("decisions") or {}
    decisions[req.key] = req.value

    questions = build_default_questionnaire()
    ok, errors = validate_decisions(questions, decisions, require_all=False)
    if not ok:
        raise HTTPException(status_code=400, detail={"validation_errors": errors})

    payload["decisions"] = decisions
    payload["updated_at"] = _now()
    cache.set(key, payload, ttl=int(payload.get("ttl_seconds") or 0) or None)

    nxt = unresolved_questions(questions, decisions)
    next_q = _question_to_dict(nxt[0]) if nxt else None

    if event_bus is not None and getattr(event_bus, "enabled", False):
        event_bus.publish("dialog", "dialog.answer.recorded", {"session_id": session_id, "key": req.key})
        if next_q is None:
            event_bus.publish("dialog", "dialog.session.completed", {"session_id": session_id})

    return SessionInfo(
        session_id=session_id,
        schema_version=payload.get("schema_version") or SCHEMA_VERSION,
        decisions=decisions,
        next_question=next_q,
        complete=next_q is None,
    )


@router.post("/sessions/{session_id}/export-project-init")
def export_project_init(session_id: str, req: ExportProjectInitRequest, _: bool = Depends(verify_api_key)) -> Dict[str, Any]:
    cache = get_cache()
    payload = cache.get(_cache_key(session_id))
    if not payload:
        raise HTTPException(status_code=404, detail="Dialog session not found")

    decisions = payload.get("decisions") or {}

    template = dict(req.template or {})
    if "format" in decisions:
        template["format"] = decisions["format"]
    if "variants" in decisions:
        v = decisions["variants"]
        if v == "both":
            template["variants"] = ["color", "grayscale"]
        elif isinstance(v, list):
            template["variants"] = v
        else:
            template["variants"] = [v]
    for k in ("akt_colors", "layout_density", "sidebar_detection", "infographic_handling"):
        if k in decisions:
            template[k] = decisions[k]

    return template


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: str, _: bool = Depends(verify_api_key)):
    cache = get_cache()
    cache.delete(_cache_key(session_id))
    return None
