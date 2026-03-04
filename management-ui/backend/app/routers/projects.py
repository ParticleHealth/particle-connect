import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.particle_client import (
    ParticleAPIError,
    ParticleAuthError,
    particle_client,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["projects"])


class ProjectAddress(BaseModel):
    line1: str = ""
    city: str = ""
    state: str = ""
    postal_code: str = ""


class CreateProjectRequest(BaseModel):
    display_name: str
    npi: str
    state: str = "STATE_ACTIVE"
    commonwell_type: str = "COMMONWELL_TYPE_POSTACUTECARE"
    address: ProjectAddress | None = None


class UpdateProjectRequest(BaseModel):
    state: str | None = None
    display_name: str | None = None
    npi: str | None = None
    address: ProjectAddress | None = None


def _handle_error(exc: Exception):
    if isinstance(exc, ParticleAuthError):
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    if isinstance(exc, ParticleAPIError):
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    raise HTTPException(status_code=502, detail=f"Unexpected error: {exc}") from exc


@router.get("")
async def list_projects():
    """List all projects."""
    try:
        return await particle_client.request("GET", "/v1/projects")
    except Exception as exc:
        _handle_error(exc)


@router.post("", status_code=201)
async def create_project(body: CreateProjectRequest):
    """Create a new project."""
    project = {
        "display_name": body.display_name,
        "npi": body.npi,
        "state": body.state,
        "commonwell_type": body.commonwell_type,
    }
    if body.address:
        project["address"] = body.address.model_dump(exclude_none=True)
    try:
        return await particle_client.request(
            "POST", "/v1/projects", json={"project": project}
        )
    except Exception as exc:
        _handle_error(exc)


@router.get("/{project_id}")
async def get_project(project_id: str):
    """Get project details."""
    try:
        return await particle_client.request("GET", f"/v1/projects/{project_id}")
    except Exception as exc:
        _handle_error(exc)


@router.patch("/{project_id}")
async def update_project(project_id: str, body: UpdateProjectRequest):
    """Update a project (e.g., activate/deactivate)."""
    payload = body.model_dump(exclude_none=True)
    if "address" in payload and body.address:
        payload["address"] = body.address.model_dump(exclude_none=True)
    try:
        return await particle_client.request(
            "PATCH", f"/v1/projects/{project_id}", json=payload
        )
    except Exception as exc:
        _handle_error(exc)
