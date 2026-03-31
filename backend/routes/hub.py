"""Hub validation endpoint - stateless math enrichment for hub slot data."""

import json

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any, Dict, Optional

from core.hub_validator import validate_and_enrich_control

router = APIRouter(prefix="/api/hub", tags=["hub"])

SLOT_VALIDATORS = {
    "control": validate_and_enrich_control,
}

MAX_PAYLOAD_BYTES = 100_000  # 100 KB


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

    # Size guard — reject excessively large payloads before expensive math
    try:
        payload_size = len(json.dumps(request.data))
        if payload_size > MAX_PAYLOAD_BYTES:
            return HubValidateResponse(
                success=False,
                error=f"Payload too large ({payload_size // 1000}KB > {MAX_PAYLOAD_BYTES // 1000}KB limit)"
            )
    except (TypeError, ValueError):
        pass  # Non-serializable data handled by validators

    result = validator(request.data)
    return HubValidateResponse(**result)
