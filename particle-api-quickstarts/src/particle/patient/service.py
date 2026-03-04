"""Patient service for Particle Health API operations.

This module provides PatientService which wraps the HTTP client
for patient-related operations.

Usage:
    from particle.core import ParticleSettings, ParticleHTTPClient
    from particle.patient import PatientService, PatientRegistration, Gender

    settings = ParticleSettings()
    with ParticleHTTPClient(settings) as client:
        service = PatientService(client)
        patient = PatientRegistration(
            given_name="Kam",
            family_name="Quark",
            date_of_birth="1954-12-01",
            gender=Gender.MALE,
            postal_code="11111",
            address_city="Brooklyn",
            address_state="New York",
        )
        response = service.register(patient)
        print(f"Patient ID: {response.particle_patient_id}")
"""

from __future__ import annotations

from particle.core import ParticleHTTPClient

from .models import PatientRegistration, PatientResponse


class PatientService:
    """Patient registration and management via Particle Health API."""

    def __init__(self, client: ParticleHTTPClient) -> None:
        """Initialize with an HTTP client.

        Args:
            client: Configured ParticleHTTPClient instance
        """
        self._client = client

    def register(self, patient: PatientRegistration) -> PatientResponse:
        """Register a patient with Particle Health.

        Idempotency behavior (handled by Particle API):
        - Same patient_id + same demographics = updates existing (success)
        - Same patient_id + different demographics = overlay error
        - New patient_id = creates new patient

        Args:
            patient: Validated patient registration data

        Returns:
            PatientResponse with particle_patient_id

        Raises:
            ParticleValidationError: If Particle API rejects the data
            ParticleAPIError: For other API errors
        """
        payload = patient.model_dump(mode="json", exclude_none=True)
        response = self._client.request("POST", "/api/v2/patients", json=payload)
        return PatientResponse.model_validate(response)
