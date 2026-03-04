"""Particle Health sandbox API client."""

import time
import httpx
from config import SANDBOX_BASE_URL, CLIENT_ID, CLIENT_SECRET, SCOPE


class ParticleClient:
    """Handles authentication and API calls to Particle Health sandbox."""

    def __init__(self):
        self.base_url = SANDBOX_BASE_URL
        self.token = None
        self.http = httpx.Client(timeout=60.0)

    def authenticate(self):
        """Get JWT token from Particle auth endpoint."""
        print("Authenticating with Particle sandbox...")
        resp = self.http.get(
            f"{self.base_url}/auth",
            headers={
                "client-id": CLIENT_ID,
                "client-secret": CLIENT_SECRET,
                "scope": SCOPE,
                "accept": "text/plain",
            },
        )
        resp.raise_for_status()
        self.token = resp.text.strip()
        print("Authentication successful.")
        return self.token

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def register_patient(self, demographics: dict) -> dict:
        """Register a patient and return the response with particle_patient_id."""
        print(f"Registering patient: {demographics['given_name']} {demographics['family_name']}...")
        resp = self.http.post(
            f"{self.base_url}/api/v2/patients",
            headers=self._headers(),
            json=demographics,
        )
        if resp.status_code >= 400:
            print(f"  Response status: {resp.status_code}")
            print(f"  Response body: {resp.text}")
            resp.raise_for_status()
        data = resp.json()
        print(f"Patient registered. Particle ID: {data.get('particle_patient_id', 'N/A')}")
        return data

    def submit_query(self, patient_id: str, purpose_of_use: str = "TREATMENT") -> dict:
        """Submit a clinical data query for a patient."""
        print(f"Submitting query for patient {patient_id}...")
        resp = self.http.post(
            f"{self.base_url}/api/v2/patients/{patient_id}/query",
            headers=self._headers(),
            json={"purpose_of_use": purpose_of_use},
        )
        resp.raise_for_status()
        data = resp.json()
        print(f"Query submitted. Query ID: {data.get('query_id', 'N/A')}")
        return data

    def get_query_status(self, patient_id: str) -> dict:
        """Check the status of a patient query."""
        resp = self.http.get(
            f"{self.base_url}/api/v2/patients/{patient_id}/query",
            headers=self._headers(),
        )
        resp.raise_for_status()
        return resp.json()

    def wait_for_query(self, patient_id: str, max_wait: int = 300, poll_interval: int = 10) -> dict:
        """Poll query status until complete, partial, or failed.

        Handles initial 404s (propagation delay after submission).
        """
        print("Waiting for query to complete (initial 5s delay for propagation)...")
        time.sleep(5)
        elapsed = 5
        while elapsed < max_wait:
            try:
                status_resp = self.get_query_status(patient_id)
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404 and elapsed < 30:
                    print(f"  [{elapsed}s] Query not yet available (404), retrying...")
                    time.sleep(poll_interval)
                    elapsed += poll_interval
                    continue
                raise

            status = status_resp.get("state", status_resp.get("status", "UNKNOWN"))
            print(f"  [{elapsed}s] Query status: {status}")

            if status in ("COMPLETE", "PARTIAL", "FAILED"):
                return status_resp

            time.sleep(poll_interval)
            elapsed += poll_interval

        raise TimeoutError(f"Query did not complete within {max_wait} seconds.")

    def get_flat_data(self, patient_id: str) -> dict:
        """Retrieve flat (denormalized) data for a patient."""
        print(f"Retrieving flat data for patient {patient_id}...")
        resp = self.http.get(
            f"{self.base_url}/api/v2/patients/{patient_id}/flat",
            headers=self._headers(),
        )
        resp.raise_for_status()
        data = resp.json()
        resource_types = list(data.keys()) if isinstance(data, dict) else []
        print(f"Flat data retrieved. Resource types: {resource_types}")
        return data

    def close(self):
        self.http.close()
