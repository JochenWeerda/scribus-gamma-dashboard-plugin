"""Quality Check API endpoints.

Thin wrappers around `packages.quality_check` to support plugin/backend workflows.
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status, Header
from pydantic import BaseModel, Field

from config import config
from packages.event_bus import get_event_bus
from packages.quality_check import check_amazon_constraints, run_preflight

router = APIRouter(prefix="/v1/quality", tags=["quality"])


def verify_api_key(x_api_key: str = Header(None, alias="X-API-Key")):
    if not config.API_KEY_ENABLED:
        return True
    if not x_api_key or x_api_key != config.API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API key")
    return True


class LayoutRequest(BaseModel):
    layout_json: Dict[str, Any]


class PreflightResponse(BaseModel):
    valid: bool
    errors: List[str] = Field(default_factory=list)


class PreflightRequest(LayoutRequest):
    checks: List[str] = Field(default_factory=list, description="Optional list of semantic checks to run")


@router.post("/preflight", response_model=PreflightResponse)
def preflight(req: PreflightRequest, _: bool = Depends(verify_api_key)) -> PreflightResponse:
    ok, errors = run_preflight(req.layout_json, checks=req.checks or None)

    event_bus = get_event_bus() if config.EVENT_BUS_ENABLED else None
    if event_bus is not None and getattr(event_bus, "enabled", False):
        event_bus.publish("quality", "quality.preflight.checked", {"valid": bool(ok)})

    return PreflightResponse(valid=bool(ok), errors=list(errors[:100]))


class AmazonResponse(BaseModel):
    valid: bool
    errors: List[str] = Field(default_factory=list)


@router.post("/amazon", response_model=AmazonResponse)
def amazon(req: LayoutRequest, _: bool = Depends(verify_api_key)) -> AmazonResponse:
    ok, errors = check_amazon_constraints(req.layout_json)

    event_bus = get_event_bus() if config.EVENT_BUS_ENABLED else None
    if event_bus is not None and getattr(event_bus, "enabled", False):
        event_bus.publish("quality", "quality.amazon.checked", {"valid": bool(ok)})

    return AmazonResponse(valid=bool(ok), errors=list(errors[:100]))


class QualityCheckResponse(BaseModel):
    preflight_valid: bool
    preflight_errors: List[str] = Field(default_factory=list)
    amazon_valid: bool
    amazon_errors: List[str] = Field(default_factory=list)


@router.post("/check", response_model=QualityCheckResponse)
def check(req: PreflightRequest, _: bool = Depends(verify_api_key)) -> QualityCheckResponse:
    pre_ok, pre_errs = run_preflight(req.layout_json, checks=req.checks or None)
    amz_ok, amz_errs = check_amazon_constraints(req.layout_json)

    event_bus = get_event_bus() if config.EVENT_BUS_ENABLED else None
    if event_bus is not None and getattr(event_bus, "enabled", False):
        event_bus.publish(
            "quality",
            "quality.check.completed",
            {"preflight_valid": bool(pre_ok), "amazon_valid": bool(amz_ok)},
        )

    return QualityCheckResponse(
        preflight_valid=bool(pre_ok),
        preflight_errors=list(pre_errs[:100]),
        amazon_valid=bool(amz_ok),
        amazon_errors=list(amz_errs[:100]),
    )
