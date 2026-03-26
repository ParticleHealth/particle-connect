"""Async Particle Health API client for auth + flat data retrieval.

Adapted from care-coordination-voice/particle_client.py with async support
for FastAPI compatibility.
"""

import asyncio
import httpx

from config import (
    PARTICLE_BASE_URL,
    PARTICLE_CLIENT_ID,
    PARTICLE_CLIENT_SECRET,
    PARTICLE_SCOPE,
)


class ParticleClient:
    """Handles authentication and flat data retrieval from Particle sandbox."""

    def __init__(self):
        self.base_url = PARTICLE_BASE_URL
        self.token = None
        self.http = httpx.AsyncClient(timeout=60.0)

    async def authenticate(self):
        resp = await self.http.get(
            f"{self.base_url}/auth",
            headers={
                "client-id": PARTICLE_CLIENT_ID,
                "client-secret": PARTICLE_CLIENT_SECRET,
                "scope": PARTICLE_SCOPE,
                "accept": "text/plain",
            },
        )
        resp.raise_for_status()
        self.token = resp.text.strip()
        return self.token

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def register_patient(self, demographics: dict) -> dict:
        resp = await self.http.post(
            f"{self.base_url}/api/v2/patients",
            headers=self._headers(),
            json=demographics,
        )
        resp.raise_for_status()
        return resp.json()

    async def submit_query(self, patient_id: str) -> dict:
        resp = await self.http.post(
            f"{self.base_url}/api/v2/patients/{patient_id}/query",
            headers=self._headers(),
            json={"purpose_of_use": "TREATMENT"},
        )
        resp.raise_for_status()
        return resp.json()

    async def wait_for_query(self, patient_id: str, max_wait: int = 300) -> dict:
        await asyncio.sleep(5)
        elapsed = 5
        while elapsed < max_wait:
            resp = await self.http.get(
                f"{self.base_url}/api/v2/patients/{patient_id}/query",
                headers=self._headers(),
            )
            if resp.status_code == 404 and elapsed < 30:
                await asyncio.sleep(10)
                elapsed += 10
                continue
            resp.raise_for_status()
            data = resp.json()
            status = data.get("state", data.get("status", "UNKNOWN"))
            if status in ("COMPLETE", "PARTIAL", "FAILED"):
                return data
            await asyncio.sleep(10)
            elapsed += 10
        raise TimeoutError(f"Query did not complete within {max_wait}s")

    async def get_flat_data(self, patient_id: str) -> dict:
        resp = await self.http.get(
            f"{self.base_url}/api/v2/patients/{patient_id}/flat",
            headers=self._headers(),
        )
        resp.raise_for_status()
        return resp.json()

    async def close(self):
        await self.http.aclose()
