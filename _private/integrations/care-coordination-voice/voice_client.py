"""Retell AI voice client for outbound care coordination calls.

Handles agent creation, outbound call initiation, and call status retrieval.
Swap this file for a Vapi equivalent if using Vapi instead.

Retell docs: https://docs.retellai.com/api-references
"""

import httpx
from config import RETELL_API_KEY, RETELL_BASE_URL, RETELL_FROM_NUMBER, WEBHOOK_URL


# Tool definitions the voice agent can call mid-conversation.
# Retell invokes these as function calls; your webhook_server.py handles them.
AGENT_TOOLS = [
    {
        "type": "end_call",
        "name": "schedule_followup_call",
        "description": (
            "Patient is doing well. Schedule a follow-up check-in call. "
            "Use this when the patient reports no concerns and is recovering normally."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "days_from_now": {
                    "type": "integer",
                    "description": "Days until next check-in call (3, 7, or 14)",
                },
                "notes": {
                    "type": "string",
                    "description": "Brief summary of patient status from the call",
                },
            },
            "required": ["days_from_now", "notes"],
        },
    },
    {
        "type": "end_call",
        "name": "schedule_appointment",
        "description": (
            "Patient needs a follow-up appointment with a provider. "
            "Use this when the patient needs to see a doctor but is not in immediate danger."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "Why the appointment is needed",
                },
                "urgency": {
                    "type": "string",
                    "enum": ["routine", "soon", "urgent"],
                    "description": "How soon the appointment should be",
                },
                "provider_type": {
                    "type": "string",
                    "description": "Type of provider (PCP, specialist, etc.)",
                },
            },
            "required": ["reason", "urgency"],
        },
    },
    {
        "type": "end_call",
        "name": "escalate_to_coordinator",
        "description": (
            "Something needs immediate human attention. Use this for red flags, "
            "possible readmission, patient distress, or emergency symptoms."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "Why escalation is needed",
                },
                "priority": {
                    "type": "string",
                    "enum": ["standard", "high", "critical"],
                    "description": "Urgency level",
                },
            },
            "required": ["reason", "priority"],
        },
    },
]


class RetellVoiceClient:
    """Manages Retell AI agents and outbound phone calls."""

    def __init__(self, api_key: str = RETELL_API_KEY):
        if not api_key:
            raise ValueError(
                "RETELL_API_KEY is not set. Get one at https://www.retellai.com"
            )
        self.http = httpx.Client(
            base_url=RETELL_BASE_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    def create_agent(self, system_prompt: str, voice_id: str = "11labs-Adrian") -> dict:
        """Create a Retell agent configured for care coordination calls.

        Retell requires a two-step process:
          1. Create a Retell LLM (holds the prompt + tools)
          2. Create an Agent (holds the voice + call settings, references the LLM)

        Args:
            system_prompt: The dynamic prompt built from patient discharge data.
            voice_id: Retell voice ID. "11labs-Adrian" is a calm, professional
                      male voice. Other options: "11labs-Myra" (female),
                      "11labs-Paola" (female, warm).

        Returns:
            Agent object with agent_id and llm_id.
        """
        # Step 1: Create LLM with prompt and tools
        llm_resp = self.http.post(
            "/create-retell-llm",
            json={
                "general_prompt": system_prompt,
                "general_tools": AGENT_TOOLS,
            },
        )
        llm_resp.raise_for_status()
        llm = llm_resp.json()
        llm_id = llm["llm_id"]
        print(f"  LLM created: {llm_id}")

        # Step 2: Create agent referencing the LLM
        agent_resp = self.http.post(
            "/create-agent",
            json={
                "agent_name": "Care Coordination - Discharge Follow-up",
                "response_engine": {
                    "type": "retell-llm",
                    "llm_id": llm_id,
                },
                "voice_id": voice_id,
                "language": "en-US",
                "webhook_url": WEBHOOK_URL,
                "enable_backchannel": True,
                "interruption_sensitivity": 0.6,
                "end_call_after_silence_ms": 15000,
                "max_call_duration_ms": 300000,  # 5 minute max
            },
        )
        agent_resp.raise_for_status()
        agent = agent_resp.json()
        agent["llm_id"] = llm_id  # Track for cleanup
        print(f"  Agent created: {agent.get('agent_id')}")
        return agent

    def create_call(
        self,
        agent_id: str,
        to_number: str,
        from_number: str = RETELL_FROM_NUMBER,
        metadata: dict | None = None,
    ) -> dict:
        """Initiate an outbound phone call.

        Links the from_number to the agent (required by Retell for outbound),
        then places the call.

        Args:
            agent_id: The Retell agent to use for this call.
            to_number: Patient phone number (E.164 format: +12345678910).
            from_number: Your Retell phone number (caller ID).
            metadata: Optional dict passed through to webhooks (e.g., patient_id).

        Returns:
            Call object with call_id, status.
        """
        # Retell requires the phone number to be linked to the agent for outbound
        link_resp = self.http.patch(
            f"/update-phone-number/{from_number}",
            json={"outbound_agent_id": agent_id},
        )
        link_resp.raise_for_status()
        print(f"  Phone {from_number} linked to agent {agent_id}")

        payload = {
            "agent_id": agent_id,
            "to_number": to_number,
            "from_number": from_number,
        }
        if metadata:
            payload["metadata"] = metadata

        resp = self.http.post("/v2/create-phone-call", json=payload)
        resp.raise_for_status()
        call = resp.json()
        print(f"  Call initiated: {call.get('call_id')} → {to_number}")
        return call

    def get_call(self, call_id: str) -> dict:
        """Get call details including status, duration, transcript, and tool calls."""
        resp = self.http.get(f"/v2/get-call/{call_id}")
        resp.raise_for_status()
        return resp.json()

    def delete_agent(self, agent_id: str, llm_id: str | None = None):
        """Clean up agent and LLM after demo (they persist in Retell otherwise)."""
        resp = self.http.delete(f"/delete-agent/{agent_id}")
        resp.raise_for_status()
        print(f"  Agent deleted: {agent_id}")
        if llm_id:
            resp = self.http.delete(f"/delete-retell-llm/{llm_id}")
            resp.raise_for_status()
            print(f"  LLM deleted: {llm_id}")

    def close(self):
        self.http.close()
