"""Particle Health API client — thin wrapper for auth + flat data retrieval.

Extracted from particle-e2e/particle_client.py with only the methods needed
for the care coordination demo (no CCDA, no query submission polling).
"""

import time
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
        self.http = httpx.Client(timeout=60.0)

    def authenticate(self):
        """Get JWT token from Particle auth endpoint."""
        resp = self.http.get(
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

    def register_patient(self, demographics: dict) -> dict:
        """Register a patient and return response with particle_patient_id."""
        resp = self.http.post(
            f"{self.base_url}/api/v2/patients",
            headers=self._headers(),
            json=demographics,
        )
        resp.raise_for_status()
        return resp.json()

    def submit_query(self, patient_id: str) -> dict:
        """Submit a clinical data query for a patient."""
        resp = self.http.post(
            f"{self.base_url}/api/v2/patients/{patient_id}/query",
            headers=self._headers(),
            json={"purpose_of_use": "TREATMENT"},
        )
        resp.raise_for_status()
        return resp.json()

    def wait_for_query(self, patient_id: str, max_wait: int = 300) -> dict:
        """Poll query status until complete."""
        time.sleep(5)
        elapsed = 5
        while elapsed < max_wait:
            resp = self.http.get(
                f"{self.base_url}/api/v2/patients/{patient_id}/query",
                headers=self._headers(),
            )
            if resp.status_code == 404 and elapsed < 30:
                time.sleep(10)
                elapsed += 10
                continue
            resp.raise_for_status()
            data = resp.json()
            status = data.get("state", data.get("status", "UNKNOWN"))
            print(f"  [{elapsed}s] Query status: {status}")
            if status in ("COMPLETE", "PARTIAL", "FAILED"):
                return data
            time.sleep(10)
            elapsed += 10
        raise TimeoutError(f"Query did not complete within {max_wait}s")

    def get_flat_data(self, patient_id: str) -> dict:
        """Retrieve flat (denormalized) JSON data for a patient."""
        resp = self.http.get(
            f"{self.base_url}/api/v2/patients/{patient_id}/flat",
            headers=self._headers(),
        )
        resp.raise_for_status()
        return resp.json()

    def close(self):
        self.http.close()
