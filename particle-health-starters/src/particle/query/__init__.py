"""Query module for Particle Health API.

This module provides:
- Pydantic models for query submission (QueryRequest, QueryResponse)
- Status enums (PurposeOfUse, QueryStatus)
- QueryService for query submission, polling, and data retrieval

Usage:
    from particle.core import ParticleSettings, ParticleHTTPClient
    from particle.query import QueryService, PurposeOfUse

    settings = ParticleSettings()
    with ParticleHTTPClient(settings) as client:
        service = QueryService(client)

        # Submit query for patient data
        response = service.submit_query(
            particle_patient_id="uuid-from-registration",
            purpose_of_use=PurposeOfUse.TREATMENT,
        )
        print(f"Query status: {response.query_status.value}")

        # Wait for completion with polling
        result = service.wait_for_query_complete(
            particle_patient_id="uuid-from-registration",
            timeout_seconds=300,
        )
        print(f"Files available: {result.files_available}")
"""

from .models import PurposeOfUse, QueryRequest, QueryResponse, QueryStatus, QuerySubmitResponse
from .service import QueryService

__all__ = [
    "QueryService",
    "QueryRequest",
    "QueryResponse",
    "QuerySubmitResponse",
    "PurposeOfUse",
    "QueryStatus",
]
