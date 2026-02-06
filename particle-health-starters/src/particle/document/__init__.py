"""Document module for Particle Health API.

This module provides:
- Pydantic models for document submission (DocumentSubmission, DocumentResponse)
- DocumentType and MimeType enums
- DocumentService for document operations

Usage:
    from particle.core import ParticleSettings, ParticleHTTPClient
    from particle.document import DocumentService, DocumentSubmission, MimeType

    settings = ParticleSettings()
    with ParticleHTTPClient(settings) as client:
        service = DocumentService(client)
        document = DocumentSubmission(
            patient_id="particle-patient-id",
            document_id="my-doc-001",
            title="clinical_summary.xml",
            mime_type=MimeType.XML,
            creation_time="2020-01-01T12:30:00Z",
            format_code="urn:ihe:pcc:xphr:2007",
            class_code="11369-6",
            type_code="11369-6",
        )
        response = service.submit(document)
        print(f"Submitted: {response.document_id}")
"""

from .models import DocumentResponse, DocumentSubmission, DocumentType, MimeType
from .service import DocumentService

__all__ = [
    "DocumentService",
    "DocumentSubmission",
    "DocumentResponse",
    "DocumentType",
    "MimeType",
]
