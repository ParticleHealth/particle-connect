"""Patient module for Particle Health API.

This module provides:
- Pydantic models for patient registration (PatientRegistration, PatientResponse)
- Gender enum for patient demographics
- PatientService for patient operations

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

from .models import Gender, PatientRegistration, PatientResponse
from .service import PatientService

__all__ = [
    "PatientService",
    "PatientRegistration",
    "PatientResponse",
    "Gender",
]
