import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.particle_client import (
    ParticleAPIError,
    ParticleAuthError,
    particle_client,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/service-accounts", tags=["service-accounts"])


class PolicyBinding(BaseModel):
    role: str
    resources: list[str]


class SetPolicyRequest(BaseModel):
    bindings: list[PolicyBinding]


def _handle_error(exc: Exception):
    if isinstance(exc, ParticleAuthError):
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    if isinstance(exc, ParticleAPIError):
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    raise HTTPException(status_code=502, detail=f"Unexpected error: {exc}") from exc


@router.get("")
async def list_service_accounts():
    """List all service accounts."""
    try:
        return await particle_client.request("GET", "/v1/serviceaccounts")
    except Exception as exc:
        _handle_error(exc)


class CreateServiceAccountRequest(BaseModel):
    display_name: str = "New Service Account"


@router.post("", status_code=201)
async def create_service_account(body: CreateServiceAccountRequest | None = None):
    """Create a new service account."""
    name = body.display_name if body else "New Service Account"
    try:
        return await particle_client.request(
            "POST",
            "/v1/serviceaccounts",
            json={"service_account": {"display_name": name}},
        )
    except Exception as exc:
        _handle_error(exc)


@router.get("/{account_id}")
async def get_service_account(account_id: str):
    """Get service account details."""
    try:
        return await particle_client.request(
            "GET", f"/v1/serviceaccounts/{account_id}"
        )
    except Exception as exc:
        _handle_error(exc)


@router.post("/{account_id}/policy")
async def set_policy(account_id: str, body: SetPolicyRequest):
    """Set IAM policy for a service account."""
    payload = {
        "bindings": [b.model_dump() for b in body.bindings],
    }
    try:
        return await particle_client.request(
            "POST",
            f"/v1/serviceaccounts/{account_id}:setPolicy",
            json=payload,
        )
    except Exception as exc:
        _handle_error(exc)


@router.get("/{account_id}/policy")
async def get_policy(account_id: str):
    """Get IAM policy for a service account."""
    try:
        return await particle_client.request(
            "GET", f"/v1/serviceaccounts/{account_id}:getPolicy"
        )
    except Exception as exc:
        _handle_error(exc)
