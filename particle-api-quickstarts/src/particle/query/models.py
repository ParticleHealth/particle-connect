"""Pydantic models for query submission and status with Particle Health API.

This module provides validated data models for query operations:
- PurposeOfUse: Enum for TREATMENT/PAYMENT/OPERATIONS
- QueryStatus: Enum for query processing states
- QueryRequest: Input model for query submission
- QueryResponse: Response model with query status and file counts

Query Flow:
1. Submit query with PurposeOfUse (POST /api/v2/patients/{id}/query)
2. Poll status until COMPLETE or PARTIAL (GET /api/v2/patients/{id}/query)
3. Retrieve data in desired format (CCDA/FHIR/Flat)
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class PurposeOfUse(str, Enum):
    """Valid purpose of use values for query submission.

    Required for HIPAA compliance when requesting patient data.
    - TREATMENT: Healthcare operations, diagnosis, treatment planning
    - PAYMENT: Insurance claims, billing verification
    - OPERATIONS: Quality improvement, case management
    """

    TREATMENT = "TREATMENT"
    PAYMENT = "PAYMENT"
    OPERATIONS = "OPERATIONS"


class QueryStatus(str, Enum):
    """Query processing status from Particle API.

    Status progression: PENDING -> PROCESSING -> (COMPLETE | PARTIAL | FAILED)
    - PENDING: Query submitted, not yet started
    - PROCESSING: Query in progress, fetching from sources
    - COMPLETE: All sources responded, data ready
    - PARTIAL: Some sources responded, partial data available
    - FAILED: Query failed, check error_message
    """

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


class QueryRequest(BaseModel):
    """Request model for query submission.

    Attributes:
        purpose_of_use: Reason for data request (default: TREATMENT)
    """

    purpose_of_use: PurposeOfUse = PurposeOfUse.TREATMENT


class QuerySubmitResponse(BaseModel):
    """Response model from query submission endpoint.

    The POST /api/v2/patients/{id}/query endpoint returns only the
    particle_patient_id confirming the query was accepted.

    Attributes:
        particle_patient_id: Particle's UUID for the patient
    """

    particle_patient_id: str

    model_config = ConfigDict(extra="ignore")


class QueryResponse(BaseModel):
    """Response model from query status endpoint.

    Contains query processing status and file availability counts.
    Uses extra="ignore" to gracefully handle unknown fields in API response.

    Attributes:
        query_status: Current processing state (mapped from API's "state" field)
        files_available: Number of files ready for download (if provided by API)
        files_downloaded: Number of files already retrieved (if provided by API)
        error_message: Error details if status is FAILED
    """

    query_status: QueryStatus = Field(validation_alias="state")
    files_available: int = 0
    files_downloaded: int = 0
    error_message: str | None = None

    model_config = ConfigDict(extra="ignore", populate_by_name=True)
