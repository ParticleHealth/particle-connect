import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.particle_client import (
    ParticleAPIError,
    ParticleAuthError,
    particle_client,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/service-accounts", tags=["credentials"])


class CreateCredentialRequest(BaseModel):
    oldCredentialTtlHours: int | None = None


def _handle_error(exc: Exception):
    if isinstance(exc, ParticleAuthError):
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    if isinstance(exc, ParticleAPIError):
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    raise HTTPException(status_code=502, detail=f"Unexpected error: {exc}") from exc


@router.post("/{account_id}/credentials", status_code=201)
async def create_credential(account_id: str, body: CreateCredentialRequest | None = None):
    """Create credentials for a service account.

    Returns clientId and clientSecret. The secret is only shown once.
    """
    payload = None
    if body and body.oldCredentialTtlHours is not None:
        payload = {"oldCredentialTtlHours": body.oldCredentialTtlHours}
    try:
        return await particle_client.request(
            "POST",
            f"/v1/serviceaccounts/{account_id}/credentials",
            json=payload,
        )
    except Exception as exc:
        _handle_error(exc)


@router.get("/{account_id}/credentials")
async def list_credentials(account_id: str):
    """List credentials for a service account."""
    try:
        return await particle_client.request(
            "GET", f"/v1/serviceaccounts/{account_id}/credentials"
        )
    except ParticleAPIError as exc:
        if exc.status_code in (405, 501):
            # Sandbox API doesn't support listing credentials
            return {"credentials": []}
        _handle_error(exc)
    except Exception as exc:
        _handle_error(exc)


@router.delete("/{account_id}/credentials/{credential_id}", status_code=204)
async def delete_credential(account_id: str, credential_id: str):
    """Delete a credential."""
    try:
        await particle_client.request(
            "DELETE",
            f"/v1/serviceaccounts/{account_id}/credentials/{credential_id}",
        )
    except Exception as exc:
        _handle_error(exc)
