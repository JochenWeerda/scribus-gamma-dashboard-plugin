"""Variant Generator API endpoints.

Thin wrappers around `packages.variant_generator` to support plugin/backend workflows.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Header
from pydantic import BaseModel, Field

from config import config
from packages.variant_generator import (
    apply_bleed,
    convert_layout_colors_to_grayscale,
    convert_layout_format,
    validate_kdp_layout,
)
from packages.layout_schema import validate_layout
from packages.event_bus import get_event_bus

router = APIRouter(prefix="/v1/variants", tags=["variants"])


def verify_api_key(x_api_key: str = Header(None, alias="X-API-Key")):
    if not config.API_KEY_ENABLED:
        return True
    if not x_api_key or x_api_key != config.API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API key")
    return True


class LayoutRequest(BaseModel):
    layout_json: Dict[str, Any]


class GrayscaleResponse(BaseModel):
    layout_json: Dict[str, Any]
    schema_valid: bool
    schema_errors: List[str] = Field(default_factory=list)


@router.post("/grayscale", response_model=GrayscaleResponse)
def to_grayscale(req: LayoutRequest, _: bool = Depends(verify_api_key)) -> GrayscaleResponse:
    out = convert_layout_colors_to_grayscale(req.layout_json)
    ok, errors = validate_layout(out)

    event_bus = get_event_bus() if config.EVENT_BUS_ENABLED else None
    if event_bus is not None and getattr(event_bus, "enabled", False):
        event_bus.publish("variants", "variants.grayscale.created", {"schema_valid": ok})

    return GrayscaleResponse(layout_json=out, schema_valid=ok, schema_errors=errors[:50])


class FormatRequest(BaseModel):
    layout_json: Dict[str, Any]
    target_format: str = Field(description="A4 | 8x11.5")


class FormatResponse(BaseModel):
    layout_json: Dict[str, Any]
    schema_valid: bool
    schema_errors: List[str] = Field(default_factory=list)


@router.post("/format", response_model=FormatResponse)
def to_format(req: FormatRequest, _: bool = Depends(verify_api_key)) -> FormatResponse:
    try:
        out = convert_layout_format(req.layout_json, target_format=req.target_format)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    ok, errors = validate_layout(out)

    event_bus = get_event_bus() if config.EVENT_BUS_ENABLED else None
    if event_bus is not None and getattr(event_bus, "enabled", False):
        event_bus.publish("variants", "variants.format.created", {"target_format": req.target_format, "schema_valid": ok})

    return FormatResponse(layout_json=out, schema_valid=ok, schema_errors=errors[:50])


class BleedRequest(BaseModel):
    layout_json: Dict[str, Any]
    bleed_mm: float = Field(default=3.0, ge=0.0, le=20.0)


class BleedResponse(BaseModel):
    layout_json: Dict[str, Any]
    schema_valid: bool
    schema_errors: List[str] = Field(default_factory=list)


@router.post("/bleed", response_model=BleedResponse)
def with_bleed(req: BleedRequest, _: bool = Depends(verify_api_key)) -> BleedResponse:
    out = apply_bleed(req.layout_json, bleed_mm=req.bleed_mm)
    ok, errors = validate_layout(out)

    event_bus = get_event_bus() if config.EVENT_BUS_ENABLED else None
    if event_bus is not None and getattr(event_bus, "enabled", False):
        event_bus.publish("variants", "variants.bleed.applied", {"bleed_mm": req.bleed_mm, "schema_valid": ok})

    return BleedResponse(layout_json=out, schema_valid=ok, schema_errors=errors[:50])


class KdpValidateRequest(BaseModel):
    layout_json: Dict[str, Any]
    safety_margin_px: float = Field(default=0.0, ge=0.0)


class KdpValidateResponse(BaseModel):
    valid: bool
    errors: List[str] = Field(default_factory=list)


@router.post("/kdp-validate", response_model=KdpValidateResponse)
def kdp_validate(req: KdpValidateRequest, _: bool = Depends(verify_api_key)) -> KdpValidateResponse:
    ok, errors = validate_kdp_layout(req.layout_json, safety_margin_px=req.safety_margin_px)

    event_bus = get_event_bus() if config.EVENT_BUS_ENABLED else None
    if event_bus is not None and getattr(event_bus, "enabled", False):
        event_bus.publish("variants", "variants.kdp.validated", {"valid": ok})

    return KdpValidateResponse(valid=ok, errors=errors[:100])

