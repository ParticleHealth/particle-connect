"""Pydantic models for document submission with Particle Health API.

This module provides validated data models for document operations:
- DocumentType: Enum for document type (CLINICAL)
- MimeType: Enum for supported MIME types (XML, PDF)
- DocumentSubmission: Input model for document submission
- DocumentResponse: Response model with submission confirmation

Document Submission:
Particle API accepts document metadata via POST /api/v1/documents.
This is typically used to submit CCDA (XML) or PDF clinical documents.

Field Descriptions:
- patient_id: Your external patient ID assigned during registration
- document_id: Your external document ID for tracking
- format_code: LOINC or IHE format code (e.g., "urn:ihe:pcc:xphr:2007")
- class_code: Document class LOINC code (e.g., "11369-6")
- type_code: Document type LOINC code (e.g., "11369-6")
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


class DocumentType(str, Enum):
    """Document type values accepted by Particle Health API.

    CLINICAL: Clinical document (e.g., CCDA, clinical PDF)
    """

    CLINICAL = "CLINICAL"


class MimeType(str, Enum):
    """MIME types for document content.

    XML: For CCDA documents (application/xml)
    PDF: For PDF documents (application/pdf)
    """

    XML = "application/xml"
    PDF = "application/pdf"


class DocumentSubmission(BaseModel):
    """Document submission request model.

    Required metadata for submitting a document to Particle Health.
    Pydantic validates all fields before API submission.

    Attributes:
        patient_id: Your external patient ID assigned during registration
        document_id: Your external document ID
        type: Document type (defaults to CLINICAL)
        title: Document filename with extension (e.g., "summary.xml")
        mime_type: Content MIME type (XML or PDF)
        creation_time: Document creation timestamp (ISO8601)
        format_code: IHE/LOINC format code
        class_code: Document class code
        type_code: Document type code
        confidentiality_code: Confidentiality level (default "N" = Normal)
        healthcare_facility_type_code: SNOMED facility type code
        practice_setting_code: SNOMED practice setting code
        service_start_time: Service period start (optional)
        service_stop_time: Service period end (optional)
    """

    # Required fields
    patient_id: str
    document_id: str
    type: DocumentType = DocumentType.CLINICAL
    title: str
    mime_type: MimeType
    creation_time: datetime
    format_code: str
    class_code: str
    type_code: str

    # Optional fields with defaults
    confidentiality_code: str = "N"
    healthcare_facility_type_code: str = "394777002"
    practice_setting_code: str = "394733009"
    service_start_time: datetime | None = None
    service_stop_time: datetime | None = None

    model_config = ConfigDict(str_strip_whitespace=True)


class DocumentResponse(BaseModel):
    """Response model from document submission.

    Contains confirmation of document submission.
    Uses extra="ignore" to gracefully handle unknown fields in API response.

    Attributes:
        document_id: Echoed document ID
        patient_id: Echoed patient ID
        status: Submission status if provided
    """

    document_id: str
    patient_id: str
    status: str | None = None

    model_config = ConfigDict(extra="ignore")


class DocumentMetadata(BaseModel):
    """Full document metadata returned by GET endpoints.

    Returned when retrieving a single document or listing patient documents.
    Contains all metadata fields submitted during document creation.

    Attributes:
        patient_id: External patient ID
        document_id: External document ID
        type: Document type (e.g., CLINICAL)
        title: Document filename
        mime_type: Content MIME type
        creation_time: Document creation timestamp
        format_code: IHE/LOINC format code
        confidentiality_code: Confidentiality level
        class_code: Document class code
        type_code: Document type code
        healthcare_facility_type_code: SNOMED facility type code
        practice_setting_code: SNOMED practice setting code
        service_start_time: Service period start (optional)
        service_stop_time: Service period end (optional)
    """

    patient_id: str
    document_id: str
    type: str | None = None
    title: str | None = None
    mime_type: str | None = None
    creation_time: str | None = None
    format_code: str | None = None
    confidentiality_code: str | None = None
    class_code: str | None = None
    type_code: str | None = None
    healthcare_facility_type_code: str | None = None
    practice_setting_code: str | None = None
    service_start_time: str | None = None
    service_stop_time: str | None = None

    model_config = ConfigDict(extra="ignore")
