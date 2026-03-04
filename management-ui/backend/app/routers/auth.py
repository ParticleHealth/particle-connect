import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.particle_client import ParticleAuthError, particle_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


class AuthStatus(BaseModel):
    authenticated: bool
    environment: str


class SwitchRequest(BaseModel):
    environment: str


@router.post("/connect")
async def connect():
    """Authenticate with Particle using .env credentials."""
    try:
        await particle_client.connect()
    except ParticleAuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return {
        "authenticated": True,
        "environment": particle_client.environment,
    }


@router.get("/status", response_model=AuthStatus)
async def auth_status():
    """Check whether the backend currently holds a valid JWT."""
    return AuthStatus(
        authenticated=particle_client.is_authenticated,
        environment=particle_client.environment,
    )


@router.post("/switch")
async def switch_environment(body: SwitchRequest):
    """Switch between sandbox and production environments."""
    try:
        await particle_client.switch_environment(body.environment)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ParticleAuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return {
        "authenticated": True,
        "environment": particle_client.environment,
    }
