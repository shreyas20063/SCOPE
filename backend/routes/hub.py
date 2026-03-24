"""Hub validation endpoint - stateless math enrichment for hub slot data."""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any, Dict, Optional

from core.hub_validator import (
    validate_and_enrich_control,
    validate_signal_slot,
    validate_circuit_slot,
    validate_optics_slot,
)

router = APIRouter(prefix="/api/hub", tags=["hub"])

SLOT_VALIDATORS = {
    "control": validate_and_enrich_control,
    "signal": validate_signal_slot,
    "circuit": validate_circuit_slot,
    "optics": validate_optics_slot,
}


class HubValidateRequest(BaseModel):
    slot: str
    data: Dict[str, Any]


class HubValidateResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@router.post("/validate", response_model=HubValidateResponse)
async def validate_hub_data(request: HubValidateRequest):
    """Validate and enrich hub slot data. Stateless, no server-side storage."""
    validator = SLOT_VALIDATORS.get(request.slot)
    if not validator:
        return HubValidateResponse(success=False, error=f"Unknown slot: {request.slot}")

    result = validator(request.data)
    return HubValidateResponse(**result)
