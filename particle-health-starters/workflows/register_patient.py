#!/usr/bin/env python3
"""Example: Register a patient with Particle Health API.

This script demonstrates:
1. Loading configuration from environment variables
2. Creating a validated patient registration request
3. Registering the patient via the Particle API
4. Handling the response (including idempotent re-registration)

Prerequisites:
    Set these environment variables:
    - PARTICLE_CLIENT_ID: Your Particle client ID
    - PARTICLE_CLIENT_SECRET: Your Particle client secret
    - PARTICLE_SCOPE_ID: Your Particle scope ID

Usage:
    # Set environment variables first
    export PARTICLE_CLIENT_ID=your-client-id
    export PARTICLE_CLIENT_SECRET=your-secret
    export PARTICLE_SCOPE_ID=your-scope

    # Run with default demo patient
    python workflows/register_patient.py

    # Run with JSON file
    python workflows/register_patient.py patient.json

    # Run with inline JSON
    python workflows/register_patient.py '{"given_name": "John", "family_name": "Doe", ...}'

Notes:
    - Uses sandbox environment by default (PARTICLE_BASE_URL)
    - The patient_id field enables idempotent registration:
      - Same patient_id + same demographics = update (success)
      - Same patient_id + different demographics = error
      - Different patient_id = new patient
"""

import json
import sys

from particle.core import (
    ParticleAPIError,
    ParticleHTTPClient,
    ParticleSettings,
    ParticleValidationError,
    configure_logging,
)
from particle.patient import Gender, PatientRegistration, PatientService

# Default demo patient data
DEFAULT_PATIENT = {
    "given_name": "Elvira",
    "family_name": "Valadez-Nucleus",
    "date_of_birth": "1970-12-26",
    "gender": "FEMALE",
    "postal_code": "02215",
    "address_city": "Boston",
    "address_state": "Massachusetts",
    "patient_id": "test-elvira-valadez",
    "address_lines": [""],
    "ssn": "123-45-6789",
    "telephone": "1-234-567-8910",
}


def load_patient_data() -> dict:
    """Load patient data from argument or use default."""
    if len(sys.argv) < 2:
        print("Using default demo patient data")
        return DEFAULT_PATIENT

    arg = sys.argv[1]

    # Check if it's a JSON file
    if arg.endswith(".json"):
        print(f"Loading patient data from: {arg}")
        with open(arg) as f:
            return json.load(f)

    # Try parsing as inline JSON
    try:
        print("Parsing inline JSON")
        return json.loads(arg)
    except json.JSONDecodeError:
        print(f"Error: Could not parse argument as JSON file or JSON string: {arg}")
        sys.exit(1)


def main() -> None:
    """Run patient registration example."""
    # Enable structured logging (optional, but helpful for debugging)
    configure_logging()

    # Load settings from environment variables
    # Raises ValidationError if required vars are missing
    settings = ParticleSettings()
    print(f"Using Particle API at: {settings.base_url}")

    # Load patient data from argument or default
    data = load_patient_data()

    # Convert gender string to enum
    if "gender" in data and isinstance(data["gender"], str):
        data["gender"] = Gender[data["gender"].upper()]

    # Create patient data with validation
    # Pydantic validates all fields before we even call the API
    patient = PatientRegistration(**data)

    print(f"Registering patient: {patient.given_name} {patient.family_name}")

    # Register patient via API
    try:
        with ParticleHTTPClient(settings) as client:
            service = PatientService(client)
            response = service.register(patient)

        # Success!
        print("\nPatient registered successfully!")
        print(f"  Particle Patient ID: {response.particle_patient_id}")
        print(f"  Your Patient ID: {response.patient_id}")
        print("\nUse the Particle Patient ID for subsequent queries.")

    except ParticleValidationError as e:
        # API rejected the data (e.g., invalid field format)
        print(f"\nValidation error: {e.message}")
        if e.errors:
            for error in e.errors:
                print(f"  - {error}")

    except ParticleAPIError as e:
        # Other API error (e.g., overlay detection for duplicate with different data)
        print(f"\nAPI error ({e.status_code}): {e.message}")
        if e.response_body:
            print(f"  Details: {e.response_body}")


if __name__ == "__main__":
    main()
