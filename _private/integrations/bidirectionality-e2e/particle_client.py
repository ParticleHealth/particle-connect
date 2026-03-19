"""Particle Health API client for bi-directionality E2E test.

Handles authentication, patient registration, and the full document
lifecycle: submit, retrieve, list, and delete.
"""

import json
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
        print(f"  Token: {self.token[:20]}...")
        print("Authentication successful.")
        return self.token

    def _headers(self, accept="application/json"):
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": accept,
        }

    def register_patient(self, demographics: dict) -> dict:
        """Register a patient and return the response with particle_patient_id."""
        name = f"{demographics['given_name']} {demographics['family_name']}"
        print(f"Registering patient: {name}...")
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

    def submit_document(self, metadata: dict, file_content: bytes) -> dict:
        """Submit a clinical document via multipart upload.

        Args:
            metadata: Document metadata dict (patient_id, document_id, etc.)
            file_content: Raw file bytes

        Returns:
            API response dict
        """
        title = metadata.get("title", "document")
        mime_type = metadata.get("mime_type", "application/xml")

        print(f"Submitting document: {title}...")
        resp = self.http.post(
            f"{self.base_url}/api/v1/documents",
            headers={"Authorization": f"Bearer {self.token}"},
            files={
                "metadata": (None, json.dumps(metadata), "application/json"),
                "file": (title, file_content, mime_type),
            },
        )
        if resp.status_code >= 400:
            print(f"  Response status: {resp.status_code}")
            print(f"  Response body: {resp.text}")
            resp.raise_for_status()
        data = resp.json()
        print(f"  Document submitted successfully.")
        return data

    def get_document(self, document_id: str) -> dict:
        """Retrieve metadata for a submitted document."""
        print(f"Retrieving document: {document_id}...")
        resp = self.http.get(
            f"{self.base_url}/api/v1/documents/{document_id}",
            headers={"Authorization": f"Bearer {self.token}"},
        )
        if resp.status_code >= 400:
            print(f"  Response status: {resp.status_code}")
            print(f"  Response body: {resp.text}")
            resp.raise_for_status()
        data = resp.json()
        print(f"  Document retrieved successfully.")
        return data

    def list_patient_documents(self, patient_id: str) -> list:
        """List all documents for a patient."""
        print(f"Listing documents for patient: {patient_id}...")
        resp = self.http.get(
            f"{self.base_url}/api/v1/documents/patient/{patient_id}",
            headers={"Authorization": f"Bearer {self.token}"},
        )
        if resp.status_code >= 400:
            print(f"  Response status: {resp.status_code}")
            print(f"  Response body: {resp.text}")
            resp.raise_for_status()
        data = resp.json()
        if data is None:
            data = []
        print(f"  Found {len(data)} document(s).")
        return data

    def delete_document(self, document_id: str) -> str:
        """Delete a submitted document."""
        print(f"Deleting document: {document_id}...")
        resp = self.http.delete(
            f"{self.base_url}/api/v1/documents/{document_id}",
            headers={"Authorization": f"Bearer {self.token}"},
        )
        if resp.status_code >= 400:
            print(f"  Response status: {resp.status_code}")
            print(f"  Response body: {resp.text}")
            resp.raise_for_status()
        result = resp.text
        print(f"  Result: {result}")
        return result

    def close(self):
        self.http.close()
