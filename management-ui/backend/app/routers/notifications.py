import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.particle_client import (
    ParticleAPIError,
    ParticleAuthError,
    particle_client,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["notifications"])


class CreateNotificationRequest(BaseModel):
    display_name: str
    notification_type: str
    callback_url: str
    active: bool = True


class UpdateNotificationRequest(BaseModel):
    display_name: str | None = None
    callback_url: str | None = None
    active: bool | None = None


def _handle_error(exc: Exception):
    if isinstance(exc, ParticleAuthError):
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    if isinstance(exc, ParticleAPIError):
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    raise HTTPException(status_code=502, detail=f"Unexpected error: {exc}") from exc


@router.get("")
async def list_notifications():
    """List all notifications."""
    try:
        return await particle_client.request("GET", "/v1/notifications")
    except Exception as exc:
        _handle_error(exc)


@router.get("/{notification_id}")
async def get_notification(notification_id: str):
    """Get a single notification."""
    try:
        return await particle_client.request(
            "GET", f"/v1/notifications/{notification_id}"
        )
    except Exception as exc:
        _handle_error(exc)


@router.post("", status_code=201)
async def create_notification(body: CreateNotificationRequest):
    """Create a new notification config."""
    notification = {
        "display_name": body.display_name,
        "notification_type": body.notification_type,
        "callback_url": body.callback_url,
        "active": body.active,
    }
    try:
        return await particle_client.request(
            "POST", "/v1/notifications", json={"notification": notification}
        )
    except Exception as exc:
        _handle_error(exc)


@router.patch("/{notification_id}")
async def update_notification(notification_id: str, body: UpdateNotificationRequest):
    """Update a notification config."""
    payload = body.model_dump(exclude_none=True)
    update_fields = list(payload.keys())
    update_mask = ",".join(update_fields)
    try:
        return await particle_client.request(
            "PATCH",
            f"/v1/notifications/{notification_id}?update_mask={update_mask}",
            json=payload,
        )
    except Exception as exc:
        _handle_error(exc)


@router.delete("/{notification_id}", status_code=204)
async def delete_notification(notification_id: str):
    """Delete a notification config."""
    try:
        await particle_client.request(
            "DELETE", f"/v1/notifications/{notification_id}"
        )
    except Exception as exc:
        _handle_error(exc)


# ── Signature Keys ──


class CreateSignatureKeyRequest(BaseModel):
    signature_key: str


@router.post("/{notification_id}/signaturekeys", status_code=201)
async def create_signature_key(notification_id: str, body: CreateSignatureKeyRequest):
    """Create a signature key for a notification."""
    try:
        return await particle_client.request(
            "POST",
            f"/v1/notifications/{notification_id}/signaturekeys",
            json={"signature_key": {"signature_key": body.signature_key}},
        )
    except Exception as exc:
        _handle_error(exc)


@router.get("/{notification_id}/signaturekeys/{key_id}")
async def get_signature_key(notification_id: str, key_id: str):
    """Get a specific signature key."""
    try:
        return await particle_client.request(
            "GET",
            f"/v1/notifications/{notification_id}/signaturekeys/{key_id}",
        )
    except Exception as exc:
        _handle_error(exc)


@router.delete("/{notification_id}/signaturekeys/{key_id}")
async def delete_signature_key(notification_id: str, key_id: str):
    """Delete a signature key."""
    try:
        return await particle_client.request(
            "DELETE",
            f"/v1/notifications/{notification_id}/signaturekeys/{key_id}",
        )
    except Exception as exc:
        _handle_error(exc)
