"""Particle Signal ADT webhook receiver for auto-triggering ToC workflows."""

import json
import logging

from fastapi import APIRouter, HTTPException, Request

from services.signal_listener import verify_webhook_signature, parse_signal_event
from agents.orchestrator import Orchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["signal"])


@router.post("/webhooks/signal")
async def signal_webhook(request: Request):
    """Receive Particle Signal ADT events and auto-create ToC workflows."""
    db = request.app.state.db
    body = await request.body()

    # Verify signature if configured
    signature = request.headers.get("x-particle-signature", "")
    if not verify_webhook_signature(body, signature):
        raise HTTPException(401, "Invalid webhook signature")

    payload = json.loads(body)
    event = parse_signal_event(payload)

    if not event:
        return {"ok": True, "action": "ignored", "reason": "not a discharge event"}

    # Auto-create workflow for this patient
    patient_id = event["particle_patient_id"]
    facility = event.get("facility_name", "Unknown Facility")

    demographics = {
        "patient_id": f"signal-{patient_id}",
        "given_name": "Signal",
        "family_name": "Patient",
        "date_of_birth": "",
        "gender": "",
        "postal_code": "",
        "address_city": "",
        "address_state": "",
        "address_lines": [""],
        "ssn": "",
        "telephone": "",
    }

    workflow = db.create_workflow(
        patient_id=patient_id,
        patient_name=f"Signal Patient ({facility})",
        demographics=demographics,
    )
    workflow_id = workflow["id"]

    logger.info(
        "Auto-created workflow %s for Signal discharge event (patient: %s, facility: %s)",
        workflow_id, patient_id, facility,
    )

    # Auto-start data gathering
    orchestrator = Orchestrator(db)
    await orchestrator.start_workflow(workflow_id)

    return {
        "ok": True,
        "action": "workflow_created",
        "workflow_id": workflow_id,
        "patient_id": patient_id,
    }


@router.post("/signal/subscribe/{patient_id}")
async def subscribe_patient(request: Request, patient_id: str):
    """Subscribe a patient to Particle Signal ADT monitoring.

    Note: In production this would call the Particle Signal API.
    For the demo, this is a stub that returns success.
    """
    logger.info("Subscribed patient %s to Signal ADT monitoring", patient_id)
    return {
        "ok": True,
        "patient_id": patient_id,
        "subscription": "adt_monitoring",
        "note": "Demo stub — in production, calls Particle Signal API",
    }
