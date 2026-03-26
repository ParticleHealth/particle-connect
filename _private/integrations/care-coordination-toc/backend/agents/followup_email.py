"""Agent 3: Follow-up Email — composes and sends post-call email."""

import logging

from agents.base import BaseAgent
from database import Database
from services.email_client import EmailClient, compose_email

logger = logging.getLogger(__name__)


class FollowupEmailAgent(BaseAgent):
    """Composes and sends a follow-up email based on call disposition."""

    async def run(self, workflow_id: str) -> dict:
        ctx_record = self.db.get_patient_context(workflow_id)
        if not ctx_record:
            raise RuntimeError(f"No patient context for workflow {workflow_id}")

        call_result = self.db.get_call_result(workflow_id)
        context = ctx_record["context"]

        # Build disposition dict from call result
        disposition = None
        if call_result and call_result.get("disposition_action"):
            disposition = {
                "action": call_result["disposition_action"],
                "parameters": call_result.get("disposition_params") or {},
            }

        email_content = compose_email(context, disposition)

        # Determine recipient — use workflow demographics or fallback
        workflow = self.db.get_workflow(workflow_id)
        demographics = {}
        if workflow and workflow.get("patient_demographics_json"):
            import json
            demographics = json.loads(workflow["patient_demographics_json"])
        recipient = demographics.get("email", "")

        # Store as draft first
        self.db.store_email_record(
            workflow_id=workflow_id,
            recipient_email=recipient or None,
            subject=email_content["subject"],
            body_html=email_content["body_html"],
            body_text=email_content["body_text"],
            status="draft",
        )

        # Send
        client = EmailClient()
        result = await client.send(
            to=recipient or "patient@example.com",
            subject=email_content["subject"],
            body_html=email_content["body_html"],
            body_text=email_content["body_text"],
        )

        status = result.get("status", "sent")
        self.db.update_email_status(workflow_id, status)

        return {
            "recipient": recipient or "patient@example.com",
            "subject": email_content["subject"],
            "method": result.get("method", "unknown"),
            "status": status,
        }

    def validate_preconditions(self, workflow_id: str) -> bool:
        gate = self.db.get_gate_decision(workflow_id, 2)
        return gate is not None and gate["decision"] == "approved"
