"""Orchestrator — deterministic state machine for the ToC workflow pipeline."""

import asyncio
import logging

from database import Database
from models import WorkflowStatus, GateDecision

logger = logging.getLogger(__name__)

# Valid state transitions: {current_status: {event: next_status}}
TRANSITIONS = {
    "pending": {"start": "data_gathering"},
    "data_gathering": {"complete": "gate_1_pending", "fail": "failed"},
    "gate_1_pending": {"approve": "calling", "reject": "cancelled", "escalate": "cancelled"},
    "calling": {"complete": "gate_2_pending", "fail": "failed"},
    "gate_2_pending": {"approve": "emailing", "reject": "completed", "escalate": "cancelled"},
    "emailing": {"complete": "gate_3_pending", "fail": "failed"},
    "gate_3_pending": {"approve": "completed", "reject": "completed", "escalate": "cancelled"},
}

# Map status to human-readable step name
STATUS_TO_STEP = {
    "pending": "pending",
    "data_gathering": "data",
    "gate_1_pending": "gate_1",
    "calling": "call",
    "gate_2_pending": "gate_2",
    "emailing": "email",
    "gate_3_pending": "gate_3",
    "completed": "done",
    "failed": "failed",
    "cancelled": "cancelled",
}


class Orchestrator:
    """Manages workflow pipeline state transitions and agent execution."""

    def __init__(self, db: Database):
        self.db = db

    def _transition(self, workflow_id: str, event: str) -> str:
        """Apply a state transition and return the new status."""
        workflow = self.db.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        current = workflow["status"]
        valid = TRANSITIONS.get(current, {})
        new_status = valid.get(event)
        if new_status is None:
            raise ValueError(
                f"Invalid transition: {current} + {event}. "
                f"Valid events: {list(valid.keys())}"
            )

        step = STATUS_TO_STEP.get(new_status, new_status)
        self.db.update_workflow_status(workflow_id, new_status, step)
        self.db.log_event(workflow_id, f"transition:{event}", {
            "from_status": current,
            "to_status": new_status,
        })
        logger.info("Workflow %s: %s -> %s (event: %s)", workflow_id, current, new_status, event)
        return new_status

    async def start_workflow(self, workflow_id: str) -> str:
        """Start the workflow — kicks off Agent 1 in background."""
        new_status = self._transition(workflow_id, "start")
        self.db.log_event(workflow_id, "step_started", {"step": "data_gathering"})

        # Run Agent 1 in background
        asyncio.create_task(self._run_data_agent(workflow_id))
        return new_status

    async def _run_data_agent(self, workflow_id: str):
        """Execute Agent 1 and advance on completion/failure."""
        from agents.data_intelligence import DataIntelligenceAgent

        agent = DataIntelligenceAgent(self.db)
        try:
            result = await agent.run(workflow_id)
            self.db.log_event(workflow_id, "step_completed", {
                "step": "data_gathering",
                "care_gaps": len(result.get("care_gaps", [])),
            })
            self._transition(workflow_id, "complete")
        except Exception as e:
            logger.exception("Agent 1 failed for workflow %s", workflow_id)
            self._handle_failure(workflow_id, "data_gathering", str(e))

    async def _run_call_agent(self, workflow_id: str):
        """Execute Agent 2 and advance on completion/failure."""
        from agents.patient_call import PatientCallAgent

        agent = PatientCallAgent(self.db)
        try:
            result = await agent.run(workflow_id)
            self.db.log_event(workflow_id, "step_completed", {
                "step": "calling",
                "disposition": result.get("disposition"),
            })
            self._transition(workflow_id, "complete")
        except Exception as e:
            logger.exception("Agent 2 failed for workflow %s", workflow_id)
            self._handle_failure(workflow_id, "calling", str(e))

    async def _run_email_agent(self, workflow_id: str):
        """Execute Agent 3 and advance on completion/failure."""
        from agents.followup_email import FollowupEmailAgent

        agent = FollowupEmailAgent(self.db)
        try:
            result = await agent.run(workflow_id)
            self.db.log_event(workflow_id, "step_completed", {
                "step": "emailing",
                "method": result.get("method"),
            })
            self._transition(workflow_id, "complete")
        except Exception as e:
            logger.exception("Agent 3 failed for workflow %s", workflow_id)
            self._handle_failure(workflow_id, "emailing", str(e))

    def process_gate_decision(
        self, workflow_id: str, gate_number: int,
        decision: str, notes: str, decided_by: str,
    ) -> str:
        """Record gate decision and advance if approved."""
        workflow = self.db.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        expected_status = f"gate_{gate_number}_pending"
        if workflow["status"] != expected_status:
            raise ValueError(
                f"Workflow is at '{workflow['status']}', not '{expected_status}'"
            )

        # Check no existing decision
        existing = self.db.get_gate_decision(workflow_id, gate_number)
        if existing:
            raise ValueError(f"Gate {gate_number} already decided: {existing['decision']}")

        self.db.store_gate_decision(workflow_id, gate_number, decision, notes, decided_by)
        self.db.log_event(workflow_id, f"gate_{decision}", {
            "gate_number": gate_number,
            "decided_by": decided_by,
            "notes": notes,
        })

        # Map gate decision to state machine event
        event_map = {
            GateDecision.APPROVED: "approve",
            GateDecision.REJECTED: "reject",
            GateDecision.ESCALATED: "escalate",
        }
        event = event_map.get(decision, decision)
        new_status = self._transition(workflow_id, event)

        # If approved, kick off next agent
        if decision == GateDecision.APPROVED:
            self._trigger_next_agent(workflow_id, gate_number)

        return new_status

    def _trigger_next_agent(self, workflow_id: str, gate_number: int):
        """Start the next agent after a gate is approved."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No running loop (e.g., in sync tests) — skip background task
            return
        if gate_number == 1:
            loop.create_task(self._run_call_agent(workflow_id))
        elif gate_number == 2:
            loop.create_task(self._run_email_agent(workflow_id))
        # Gate 3 approval just marks completed — no next agent

    def process_webhook_call_result(
        self, workflow_id: str, call_id: str, call_data: dict
    ):
        """Handle call completion from Retell webhook (alternative to polling)."""
        duration_ms = call_data.get("call_duration_ms")
        transcript = call_data.get("transcript", "")

        disposition_action = None
        disposition_params = None
        for tc in call_data.get("tool_calls", []):
            name = tc.get("name", "")
            if name in ("schedule_followup_call", "schedule_appointment", "escalate_to_coordinator"):
                disposition_action = name
                disposition_params = tc.get("arguments", {})

        self.db.store_call_result(
            workflow_id=workflow_id,
            call_id=call_id,
            status="completed",
            duration_ms=duration_ms,
            transcript=transcript,
            disposition_action=disposition_action,
            disposition_params=disposition_params,
        )

        self.db.log_event(workflow_id, "step_completed", {
            "step": "calling",
            "disposition_action": disposition_action,
            "via": "webhook",
        })

        workflow = self.db.get_workflow(workflow_id)
        if workflow and workflow["status"] == "calling":
            self._transition(workflow_id, "complete")

    def _handle_failure(self, workflow_id: str, step: str, error: str):
        """Transition to failed state."""
        try:
            self._transition(workflow_id, "fail")
        except ValueError:
            pass
        self.db.update_workflow_status(workflow_id, "failed", step, error_message=error)
        self.db.log_event(workflow_id, "step_failed", {"step": step, "error": error})

    async def retry_workflow(self, workflow_id: str) -> str:
        """Retry a failed workflow from its failed step."""
        workflow = self.db.get_workflow(workflow_id)
        if not workflow or workflow["status"] != "failed":
            raise ValueError("Can only retry failed workflows")

        step = workflow["current_step"]
        if step == "data_gathering" or step == "data":
            self.db.update_workflow_status(workflow_id, "data_gathering", "data")
            self.db.log_event(workflow_id, "retry", {"step": "data_gathering"})
            asyncio.create_task(self._run_data_agent(workflow_id))
            return "data_gathering"
        elif step == "calling" or step == "call":
            self.db.update_workflow_status(workflow_id, "calling", "call")
            self.db.log_event(workflow_id, "retry", {"step": "calling"})
            asyncio.create_task(self._run_call_agent(workflow_id))
            return "calling"
        elif step == "emailing" or step == "email":
            self.db.update_workflow_status(workflow_id, "emailing", "email")
            self.db.log_event(workflow_id, "retry", {"step": "emailing"})
            asyncio.create_task(self._run_email_agent(workflow_id))
            return "emailing"
        else:
            raise ValueError(f"Cannot retry from step: {step}")
