"""Document service for Particle Health API operations."""

from __future__ import annotations

import json

from particle.core import ParticleHTTPClient

from .models import DocumentSubmission, DocumentResponse


class DocumentService:
    """Document submission via Particle Health API."""

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
