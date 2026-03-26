"""Async Retell AI voice client for outbound care coordination calls.

Adapted from care-coordination-voice/voice_client.py with async support.
"""

import httpx

from config import RETELL_API_KEY, RETELL_BASE_URL, RETELL_FROM_NUMBER, WEBHOOK_URL


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
    """Manages Retell AI agents and outbound phone calls (async)."""

    def __init__(self, api_key: str = RETELL_API_KEY):
        if not api_key:
            raise ValueError(
                "RETELL_API_KEY is not set. Get one at https://www.retellai.com"
            )
        self.http = httpx.AsyncClient(
            base_url=RETELL_BASE_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    async def create_agent(self, system_prompt: str, voice_id: str = "11labs-Adrian") -> dict:
        llm_resp = await self.http.post(
            "/create-retell-llm",
            json={"general_prompt": system_prompt, "general_tools": AGENT_TOOLS},
        )
        llm_resp.raise_for_status()
        llm = llm_resp.json()
        llm_id = llm["llm_id"]

        agent_resp = await self.http.post(
            "/create-agent",
            json={
                "agent_name": "Care Coordination - ToC Follow-up",
                "response_engine": {"type": "retell-llm", "llm_id": llm_id},
                "voice_id": voice_id,
                "language": "en-US",
                "webhook_url": WEBHOOK_URL,
                "enable_backchannel": True,
                "interruption_sensitivity": 0.6,
                "end_call_after_silence_ms": 15000,
                "max_call_duration_ms": 300000,
            },
        )
        agent_resp.raise_for_status()
        agent = agent_resp.json()
        agent["llm_id"] = llm_id
        return agent

    async def create_call(
        self, agent_id: str, to_number: str,
        from_number: str = RETELL_FROM_NUMBER,
        metadata: dict | None = None,
    ) -> dict:
        link_resp = await self.http.patch(
            f"/update-phone-number/{from_number}",
            json={"outbound_agent_id": agent_id},
        )
        link_resp.raise_for_status()

        payload = {
            "agent_id": agent_id,
            "to_number": to_number,
            "from_number": from_number,
        }
        if metadata:
            payload["metadata"] = metadata

        resp = await self.http.post("/v2/create-phone-call", json=payload)
        resp.raise_for_status()
        return resp.json()

    async def get_call(self, call_id: str) -> dict:
        resp = await self.http.get(f"/v2/get-call/{call_id}")
        resp.raise_for_status()
        return resp.json()

    async def delete_agent(self, agent_id: str, llm_id: str | None = None):
        resp = await self.http.delete(f"/delete-agent/{agent_id}")
        resp.raise_for_status()
        if llm_id:
            resp = await self.http.delete(f"/delete-retell-llm/{llm_id}")
            resp.raise_for_status()

    async def close(self):
        await self.http.aclose()
