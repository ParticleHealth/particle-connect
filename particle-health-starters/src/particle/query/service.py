"""Query service for Particle Health API operations.

This module provides QueryService which wraps the HTTP client
for query-related operations.

Usage:
    from particle.core import ParticleSettings, ParticleHTTPClient
    from particle.query import QueryService, PurposeOfUse

    settings = ParticleSettings()
    with ParticleHTTPClient(settings) as client:
        service = QueryService(client)

        # Submit query
        response = service.submit_query(particle_patient_id)

        # Wait for completion
        result = service.wait_for_query_complete(particle_patient_id)
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone

from particle.core import ParticleHTTPClient
from particle.core.exceptions import (
    ParticleAPIError,
    ParticleNotFoundError,
    ParticleQueryFailedError,
    ParticleQueryTimeoutError,
)

from .models import PurposeOfUse, QueryResponse, QueryStatus, QuerySubmitResponse


class QueryService:
    """Query submission, polling, and data retrieval via Particle Health API."""

    def __init__(self, client: ParticleHTTPClient) -> None:
        """Initialize with an HTTP client.

        Args:
            client: Configured ParticleHTTPClient instance
        """
        self._client = client

    def submit_query(
        self,
        particle_patient_id: str,
        purpose_of_use: PurposeOfUse = PurposeOfUse.TREATMENT,
    ) -> QuerySubmitResponse:
        """Submit a query for patient clinical data.

        Args:
            particle_patient_id: Particle's UUID from patient registration
            purpose_of_use: TREATMENT (default), PAYMENT, or OPERATIONS

        Returns:
            QuerySubmitResponse confirming the query was accepted
        """
        payload = {"purpose_of_use": purpose_of_use.value}
        response = self._client.request(
            "POST",
            f"/api/v2/patients/{particle_patient_id}/query",
            json=payload,
        )
        return QuerySubmitResponse.model_validate(response)

    def get_query_status(self, particle_patient_id: str) -> QueryResponse:
        """Check current query status.

        Args:
            particle_patient_id: Particle's UUID from patient registration

        Returns:
            QueryResponse with current status
        """
        response = self._client.request(
            "GET",
            f"/api/v2/patients/{particle_patient_id}/query",
        )
        return QueryResponse.model_validate(response)

    def wait_for_query_complete(
        self,
        particle_patient_id: str,
        timeout_seconds: float = 300.0,
        poll_interval: float = 5.0,
        max_poll_interval: float = 30.0,
    ) -> QueryResponse:
        """Poll until query completes or times out.

        Uses exponential backoff (1.5x multiplier) to avoid API hammering.

        # Future: This could be replaced by webhook-based notification.
        # For webhook support, register a callback URL during query submission,
        # and Particle would POST to that URL when the query completes.

        Args:
            particle_patient_id: Particle's patient UUID
            timeout_seconds: Maximum wait time (default 5 minutes)
            poll_interval: Initial polling interval (default 5 seconds)
            max_poll_interval: Maximum polling interval cap (default 30 seconds)

        Returns:
            QueryResponse with COMPLETE or PARTIAL status

        Raises:
            ParticleQueryTimeoutError: If timeout exceeded
            ParticleQueryFailedError: If query failed on server
        """
        deadline = datetime.now(tz=timezone.utc) + timedelta(seconds=timeout_seconds)
        current_interval = poll_interval

        while datetime.now(tz=timezone.utc) < deadline:
            try:
                status = self.get_query_status(particle_patient_id)
            except ParticleNotFoundError:
                # Query status endpoint may 404 briefly after submission
                time.sleep(current_interval)
                current_interval = min(current_interval * 1.5, max_poll_interval)
                continue

            if status.query_status in (QueryStatus.COMPLETE, QueryStatus.PARTIAL):
                return status

            if status.query_status == QueryStatus.FAILED:
                raise ParticleQueryFailedError(
                    particle_patient_id, status.error_message
                )

            # Exponential backoff with cap
            time.sleep(current_interval)
            current_interval = min(current_interval * 1.5, max_poll_interval)

        raise ParticleQueryTimeoutError(particle_patient_id, timeout_seconds)

    def get_ccda(self, particle_patient_id: str) -> bytes:
        """Retrieve CCDA data as ZIP file bytes.

        Call this after query completes (COMPLETE or PARTIAL status).
        The ZIP contains CCDA XML documents from responding sources.

        Args:
            particle_patient_id: Particle's patient UUID

        Returns:
            Raw ZIP file bytes. Save to file or process with zipfile module.

        Example:
            ccda_zip = service.get_ccda(patient_id)
            with open("ccda_data.zip", "wb") as f:
                f.write(ccda_zip)
        """
        response = self._client.request(
            "GET",
            f"/api/v2/patients/{particle_patient_id}/ccda",
        )
        # HTTP client returns {"_raw_content": bytes} for non-JSON responses
        if "_raw_content" in response:
            return response["_raw_content"]
        # 204 No Content returns {} - no CCDA data available
        if not response:
            return b""
        raise ParticleAPIError("Expected binary CCDA response", status_code=200)

    def get_fhir(self, particle_patient_id: str) -> dict:
        """Retrieve clinical data as FHIR Bundle (JSON dict).

        Returns FHIR R4 formatted clinical data. For structured parsing,
        consider using the fhir.resources library on the returned dict.

        Args:
            particle_patient_id: Particle's patient UUID

        Returns:
            FHIR Bundle as dict (JSON response)
        """
        return self._client.request(
            "GET",
            f"/api/v2/patients/{particle_patient_id}/fhir",
        )

    def get_flat(self, particle_patient_id: str) -> dict:
        """Retrieve clinical data in Particle's flat JSON format.

        Returns a simplified, denormalized view of clinical data.
        Easier to work with than FHIR for common use cases.

        Args:
            particle_patient_id: Particle's patient UUID

        Returns:
            Flat clinical data as dict (JSON response)
        """
        return self._client.request(
            "GET",
            f"/api/v2/patients/{particle_patient_id}/flat",
        )
