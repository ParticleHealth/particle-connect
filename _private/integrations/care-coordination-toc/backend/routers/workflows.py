"""Workflow CRUD and action endpoints."""

from fastapi import APIRouter, HTTPException, Request

from models import (
    CreateWorkflowRequest, WorkflowSummary, WorkflowDetail,
    PatientContextResponse, CallResultResponse, EmailRecordResponse,
    GateStatus, WorkflowEvent,
)
from agents.orchestrator import Orchestrator

router = APIRouter(prefix="/api/workflows", tags=["workflows"])


def _get_db(request: Request):
    return request.app.state.db


@router.get("")
async def list_workflows(request: Request, status: str | None = None, limit: int = 50):
    db = _get_db(request)
    workflows = db.list_workflows(status=status, limit=limit)
    return workflows


@router.post("")
async def create_workflow(request: Request, body: CreateWorkflowRequest):
    db = _get_db(request)
    demographics = {
        "patient_id": body.patient_id,
        "given_name": body.given_name,
        "family_name": body.family_name,
        "date_of_birth": body.date_of_birth,
        "gender": body.gender,
        "postal_code": body.postal_code,
        "address_city": body.address_city,
        "address_state": body.address_state,
        "address_lines": [""],
        "ssn": "123-45-6789",
        "telephone": body.telephone,
        "email": body.email,
    }
    patient_name = f"{body.given_name} {body.family_name}"
    workflow = db.create_workflow(body.patient_id, patient_name, demographics)
    return workflow


@router.get("/{workflow_id}")
async def get_workflow(request: Request, workflow_id: str):
    db = _get_db(request)
    workflow = db.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(404, f"Workflow {workflow_id} not found")

    # Enrich with related data
    ctx = db.get_patient_context(workflow_id)
    call = db.get_call_result(workflow_id)
    email = db.get_email_record(workflow_id)
    gates = db.list_gate_decisions(workflow_id)
    events = db.list_events(workflow_id)

    workflow["patient_context"] = ctx
    workflow["call_result"] = call
    workflow["email_record"] = email
    workflow["gate_decisions"] = gates
    workflow["events"] = events
    return workflow


@router.post("/{workflow_id}/start")
async def start_workflow(request: Request, workflow_id: str):
    db = _get_db(request)
    workflow = db.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(404, f"Workflow {workflow_id} not found")
    if workflow["status"] != "pending":
        raise HTTPException(409, f"Workflow is '{workflow['status']}', not 'pending'")

    orchestrator = Orchestrator(db)
    new_status = await orchestrator.start_workflow(workflow_id)
    return {"id": workflow_id, "status": new_status}


@router.post("/{workflow_id}/cancel")
async def cancel_workflow(request: Request, workflow_id: str):
    db = _get_db(request)
    workflow = db.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(404, f"Workflow {workflow_id} not found")
    if workflow["status"] in ("completed", "cancelled"):
        raise HTTPException(409, f"Workflow is already '{workflow['status']}'")

    db.update_workflow_status(workflow_id, "cancelled", "cancelled")
    db.log_event(workflow_id, "cancelled", {"previous_status": workflow["status"]})
    return {"id": workflow_id, "status": "cancelled"}


@router.post("/{workflow_id}/retry")
async def retry_workflow(request: Request, workflow_id: str):
    db = _get_db(request)
    workflow = db.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(404, f"Workflow {workflow_id} not found")
    if workflow["status"] != "failed":
        raise HTTPException(409, "Can only retry failed workflows")

    orchestrator = Orchestrator(db)
    new_status = await orchestrator.retry_workflow(workflow_id)
    return {"id": workflow_id, "status": new_status}


@router.get("/{workflow_id}/events")
async def list_events(request: Request, workflow_id: str):
    db = _get_db(request)
    return db.list_events(workflow_id)
