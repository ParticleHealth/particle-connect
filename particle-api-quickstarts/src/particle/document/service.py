"""Document service for Particle Health API operations.

Supports the full Documents API lifecycle:
- Submit (create/update) a clinical document
- Retrieve a posted document's metadata
- Delete a document
- List all documents for a patient
"""

from __future__ import annotations

import json

from particle.core import ParticleHTTPClient

from .models import DocumentMetadata, DocumentResponse, DocumentSubmission


class DocumentService:
    """Document operations via Particle Health API.

    Supports the full bi-directional document lifecycle:
    submit, get, delete, and list by patient.
    """

    def __init__(self, client: ParticleHTTPClient) -> None:
        """Initialize with an HTTP client."""
        self._client = client

    def submit(
        self,
        document: DocumentSubmission,
        file_content: bytes,
    ) -> DocumentResponse:
        """Submit a document for a patient via multipart upload.

        The Particle API expects two multipart fields:
        - "metadata": JSON string with document metadata
        - "file": the document file content

        Args:
            document: Validated document submission data
            file_content: Raw file bytes to upload

        Returns:
            DocumentResponse with submission confirmation

        Raises:
            ParticleValidationError: If Particle API rejects the data
            ParticleAPIError: For other API errors
        """
        metadata = document.model_dump(mode="json", exclude_none=True)
        metadata_json = json.dumps(metadata)

        files = {
            "metadata": (None, metadata_json, "application/json"),
            "file": (document.title, file_content, document.mime_type.value),
        }

        response = self._client.request(
            "POST", "/api/v1/documents", files=files,
        )
        return DocumentResponse.model_validate(response)

    def get(self, document_id: str) -> DocumentMetadata:
        """Retrieve metadata for a previously submitted document.

        Use this to verify a document was successfully uploaded.

        Args:
            document_id: Your external document ID

        Returns:
            DocumentMetadata with full document details

        Raises:
            ParticleNotFoundError: If document_id doesn't exist
            ParticleAPIError: For other API errors
        """
        response = self._client.request(
            "GET", f"/api/v1/documents/{document_id}",
        )
        return DocumentMetadata.model_validate(response)

    def delete(self, document_id: str) -> str:
        """Delete a previously submitted document.

        Args:
            document_id: Your external document ID

        Returns:
            Confirmation message (e.g., "delete successful")

        Raises:
            ParticleNotFoundError: If document_id doesn't exist
            ParticleAPIError: For other API errors
        """
        response = self._client.request(
            "DELETE", f"/api/v1/documents/{document_id}",
        )
        # API returns "delete successful" as a string
        if isinstance(response, str):
            return response
        return str(response)

    def list_by_patient(self, patient_id: str) -> list[DocumentMetadata]:
        """List all documents for a patient.

        Args:
            patient_id: Your external patient ID

        Returns:
            List of DocumentMetadata for all patient documents

        Raises:
            ParticleNotFoundError: If patient_id doesn't exist
            ParticleAPIError: For other API errors
        """
        response = self._client.request(
            "GET", f"/api/v1/documents/patient/{patient_id}",
        )
        if isinstance(response, list):
            return [DocumentMetadata.model_validate(doc) for doc in response]
        return []
