#!/usr/bin/env python3
"""OAuth2 E2E Test: Register patient, query, and retrieve flat data.

NOTE: Despite the filename, Particle Health does NOT use standard OAuth2
client_credentials flow. Auth is a custom GET /auth with client-id,
client-secret, and scope as custom headers, returning a plain-text JWT.
The Python SDK handles this transparently via ParticleAuth.

This script:
1. Authenticates via the SDK (custom GET /auth — NOT OAuth2)
2. Registers a patient with specified demographics
3. Submits a clinical data query and waits for completion
4. Retrieves flat JSON data
5. Prints the first 5 records from each clinical table

Prerequisites:
    Set these environment variables (or create a .env file in particle-api-quickstarts/):
    - PARTICLE_CLIENT_ID
    - PARTICLE_CLIENT_SECRET
    - PARTICLE_SCOPE_ID

Usage:
    cd particle-api-quickstarts
    source .venv/bin/activate
    python ../_private/feedback-e2e-tests/output/test5_oauth2.py
"""

import json
import sys

from particle.core import (
    ParticleAPIError,
    ParticleHTTPClient,
    ParticleQueryFailedError,
    ParticleQueryTimeoutError,
    ParticleSettings,
    ParticleValidationError,
    configure_logging,
)
from particle.patient import Gender, PatientRegistration, PatientService
from particle.query import PurposeOfUse, QueryService

# Patient demographics as specified in the task.
# address_state MUST be a two-letter abbreviation ("MA"), never full name.
PATIENT = PatientRegistration(
    given_name="Elvira",
    family_name="Valadez-Nucleus",
    date_of_birth="1985-07-03",
    gender=Gender.FEMALE,
    postal_code="02101",
    address_city="Boston",
    address_state="MA",
    address_lines=["123 Main St"],
    patient_id="test5-oauth2-e2e",
)


def print_first_5_records(flat_data: dict) -> None:
    """Print the first 5 records from each clinical table in the flat data."""
    print("\n=== First 5 Records Per Clinical Table ===\n")

    for table_name, records in sorted(flat_data.items()):
        if not isinstance(records, list):
            continue

        count = len(records)
        print(f"--- {table_name} ({count} total records) ---\n")

        for i, record in enumerate(records[:5]):
            print(f"  Record {i + 1}:")
            for key, value in record.items():
                if value not in (None, ""):
                    print(f"    {key}: {value}")
            print()

        if count == 0:
            print("  (no records)\n")


def main() -> None:
    """Run the full E2E workflow: auth, register, query, retrieve, print."""
    configure_logging()

    print("=== Particle Health E2E Test (test5_oauth2) ===\n")
    print("NOTE: Particle uses custom GET /auth with headers, NOT OAuth2.\n")

    settings = ParticleSettings()
    print(f"API: {settings.base_url}\n")

    try:
        with ParticleHTTPClient(settings) as client:
            patient_svc = PatientService(client)
            query_svc = QueryService(client)

            # Step 1: Register patient
            print("1. Registering patient...")
            print(f"   Name: {PATIENT.given_name} {PATIENT.family_name}")
            print(f"   DOB: {PATIENT.date_of_birth}")
            print(f"   Gender: {PATIENT.gender.value}")
            print(f"   Address: {PATIENT.address_lines[0]}, "
                  f"{PATIENT.address_city}, {PATIENT.address_state} "
                  f"{PATIENT.postal_code}")
            response = patient_svc.register(PATIENT)
            particle_patient_id = response.particle_patient_id
            print(f"   Particle Patient ID: {particle_patient_id}")

            # Step 2: Submit query
            print("\n2. Submitting clinical data query...")
            query_svc.submit_query(
                particle_patient_id=particle_patient_id,
                purpose_of_use=PurposeOfUse.TREATMENT,
            )
            print("   Query submitted")

            # Step 3: Wait for completion (SDK handles exponential backoff)
            print("\n3. Waiting for query to complete (may take 2-5 minutes)...")
            result = query_svc.wait_for_query_complete(
                particle_patient_id=particle_patient_id,
                timeout_seconds=300,
            )
            print(f"   Status: {result.query_status.value}")
            if result.files_available:
                print(f"   Files available: {result.files_available}")

            # Step 4: Retrieve flat data (NOT FHIR — returns 404 in sandbox)
            print("\n4. Retrieving flat JSON data...")
            flat_data = query_svc.get_flat(particle_patient_id)

            # Print resource type summary
            print("\n   Resource types returned:")
            for key, value in sorted(flat_data.items()):
                if isinstance(value, list):
                    print(f"     {key}: {len(value)} records")

            # Step 5: Print first 5 records from each table
            print_first_5_records(flat_data)

            print("=== Done! ===")

    except ParticleValidationError as e:
        print(f"\nValidation error: {e.message}")
        if e.errors:
            for error in e.errors:
                print(f"  - {error}")
        sys.exit(1)

    except ParticleQueryTimeoutError as e:
        print(f"\nQuery timed out: {e.message}")
        print("  The query may still be processing. Try again later.")
        sys.exit(1)

    except ParticleQueryFailedError as e:
        print(f"\nQuery failed: {e.message}")
        if e.error_message:
            print(f"  Details: {e.error_message}")
        sys.exit(1)

    except ParticleAPIError as e:
        print(f"\nAPI error ({e.status_code}): {e.message}")
        if e.response_body:
            print(f"  Details: {e.response_body}")
        sys.exit(1)


if __name__ == "__main__":
    main()
