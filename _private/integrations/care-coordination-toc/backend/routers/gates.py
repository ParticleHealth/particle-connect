"""Gate decision endpoints for care coordinator checkpoints."""

from fastapi import APIRouter, HTTPException, Request

from models import GateDecisionRequest
from agents.orchestrator import Orchestrator

router = APIRouter(prefix="/api/workflows", tags=["gates"])


def _get_db(request: Request):
    return request.app.state.db


@router.get("/{workflow_id}/gates")
async def list_gates(request: Request, workflow_id: str):
    db = _get_db(request)
    decisions = db.list_gate_decisions(workflow_id)
    # Build full gate status for gates 1-3
    result = []
    for gate_num in (1, 2, 3):
        existing = next((d for d in decisions if d["gate_number"] == gate_num), None)
        if existing:
            result.append({
                "gate_number": gate_num,
                "status": existing["decision"],
                "decision": existing["decision"],
                "coordinator_notes": existing.get("coordinator_notes"),
                "decided_by": existing.get("decided_by"),
                "decided_at": existing.get("decided_at"),
            })
        else:
            # Determine if gate is pending or not yet reached
            workflow = db.get_workflow(workflow_id)
            status = workflow["status"] if workflow else ""
            is_pending = status == f"gate_{gate_num}_pending"
            result.append({
                "gate_number": gate_num,
                "status": "pending" if is_pending else "not_reached",
                "decision": None,
                "coordinator_notes": None,
                "decided_by": None,
                "decided_at": None,
            })
    return result


@router.get("/{workflow_id}/gates/{gate_number}")
async def get_gate(request: Request, workflow_id: str, gate_number: int):
    if gate_number not in (1, 2, 3):
        raise HTTPException(400, "gate_number must be 1, 2, or 3")

    db = _get_db(request)
    workflow = db.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(404, f"Workflow {workflow_id} not found")

    decision = db.get_gate_decision(workflow_id, gate_number)

    # Build review data based on gate number
    review_data = {}
    if gate_number == 1:
        ctx = db.get_patient_context(workflow_id)
        if ctx:
            review_data = {
                "patient_context": ctx["context"],
                "care_gaps": ctx["care_gaps"],
            }
    elif gate_number == 2:
        call = db.get_call_result(workflow_id)
        if call:
            review_data = {"call_result": call}
        ctx = db.get_patient_context(workflow_id)
        if ctx:
            review_data["patient_context"] = ctx["context"]
    elif gate_number == 3:
        email = db.get_email_record(workflow_id)
        if email:
            review_data = {"email_record": email}

    return {
        "gate_number": gate_number,
        "status": decision["decision"] if decision else (
            "pending" if workflow["status"] == f"gate_{gate_number}_pending" else "not_reached"
        ),
        "decision": decision,
        "review_data": review_data,
    }


@router.post("/{workflow_id}/gates/{gate_number}/decide")
async def decide_gate(
    request: Request, workflow_id: str, gate_number: int,
    body: GateDecisionRequest,
):
    if gate_number not in (1, 2, 3):
        raise HTTPException(400, "gate_number must be 1, 2, or 3")

    db = _get_db(request)
    workflow = db.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(404, f"Workflow {workflow_id} not found")

    orchestrator = Orchestrator(db)
    try:
        new_status = orchestrator.process_gate_decision(
            workflow_id=workflow_id,
            gate_number=gate_number,
            decision=body.decision,
            notes=body.coordinator_notes,
            decided_by=body.decided_by,
        )
    except ValueError as e:
        raise HTTPException(409, str(e))

    return {
        "gate_number": gate_number,
        "decision": body.decision,
        "workflow_status": new_status,
    }
