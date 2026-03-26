"""Retell AI call event webhook receiver."""

from fastapi import APIRouter, Request

from agents.orchestrator import Orchestrator

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


@router.post("/call-events")
async def call_events(request: Request):
    """Receive Retell call_ended / call_analyzed events."""
    db = request.app.state.db
    event = await request.json()

    event_type = event.get("event", "unknown")
    call = event.get("call", {})
    call_id = call.get("call_id", "")
    metadata = call.get("metadata", {})
    workflow_id = metadata.get("workflow_id")

    if event_type == "call_ended" and workflow_id:
        orchestrator = Orchestrator(db)
        orchestrator.process_webhook_call_result(workflow_id, call_id, call)

    return {"ok": True}
