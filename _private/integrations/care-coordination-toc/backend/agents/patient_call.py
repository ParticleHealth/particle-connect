"""Agent 2: Patient Call — places outbound voice call via Retell AI."""

import asyncio
import logging

from agents.base import BaseAgent
from config import DEMO_OVERRIDE_PHONE
from database import Database
from services.prompt_builder import build_prompt
from services.voice_client import RetellVoiceClient

logger = logging.getLogger(__name__)


class PatientCallAgent(BaseAgent):
    """Places an outbound call and captures disposition."""

    async def run(self, workflow_id: str) -> dict:
        ctx_record = self.db.get_patient_context(workflow_id)
        if not ctx_record:
            raise RuntimeError(f"No patient context for workflow {workflow_id}")

        context = ctx_record["context"]
        prompt = build_prompt(context)

        phone = DEMO_OVERRIDE_PHONE or context.get("phone_number")
        if not phone:
            raise RuntimeError("No phone number available — set DEMO_OVERRIDE_PHONE")
        phone = _normalize_phone(phone)

        voice = RetellVoiceClient()
        agent = None
        try:
            logger.info("Creating voice agent...")
            agent = await voice.create_agent(prompt)
            agent_id = agent["agent_id"]

            logger.info("Placing call to %s...", phone)
            call = await voice.create_call(
                agent_id=agent_id,
                to_number=phone,
                metadata={
                    "workflow_id": workflow_id,
                    "patient_id": context["patient_id"],
                    "patient_name": f"{context['patient_first_name']} {context['patient_last_name']}",
                },
            )
            call_id = call["call_id"]

            logger.info("Call initiated: %s — polling for completion...", call_id)
            final = await _poll_call(voice, call_id)

            # Extract disposition
            disposition_action = None
            disposition_params = None
            tool_calls = final.get("tool_calls", [])
            for tc in tool_calls:
                name = tc.get("name", "")
                if name in ("schedule_followup_call", "schedule_appointment", "escalate_to_coordinator"):
                    disposition_action = name
                    disposition_params = tc.get("arguments", {})

            self.db.store_call_result(
                workflow_id=workflow_id,
                call_id=call_id,
                status="completed",
                duration_ms=final.get("call_duration_ms"),
                transcript=final.get("transcript", ""),
                disposition_action=disposition_action,
                disposition_params=disposition_params,
            )

            return {
                "call_id": call_id,
                "duration_ms": final.get("call_duration_ms"),
                "transcript": final.get("transcript", ""),
                "disposition": {
                    "action": disposition_action,
                    "parameters": disposition_params,
                } if disposition_action else None,
                "status": "completed",
            }
        except Exception:
            if agent:
                try:
                    await voice.delete_agent(agent["agent_id"], agent.get("llm_id"))
                except Exception:
                    pass
            raise
        finally:
            if agent:
                try:
                    await voice.delete_agent(agent["agent_id"], agent.get("llm_id"))
                except Exception:
                    pass
            await voice.close()

    def validate_preconditions(self, workflow_id: str) -> bool:
        gate = self.db.get_gate_decision(workflow_id, 1)
        return gate is not None and gate["decision"] == "approved"


async def _poll_call(voice: RetellVoiceClient, call_id: str, timeout: int = 360) -> dict:
    elapsed = 0
    while elapsed < timeout:
        call = await voice.get_call(call_id)
        status = call.get("call_status", "unknown")
        if status in ("ended", "error"):
            return call
        await asyncio.sleep(5)
        elapsed += 5
    raise TimeoutError(f"Call {call_id} did not complete within {timeout}s")


def _normalize_phone(phone: str) -> str:
    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) == 10:
        return f"+1{digits}"
    if len(digits) == 11 and digits.startswith("1"):
        return f"+{digits}"
    return phone
