#!/usr/bin/env python3
"""Hello Particle: Zero-to-data in one script.

This script runs the full Particle Health workflow end-to-end:
1. Register a demo patient
2. Submit a clinical data query
3. Poll until the query completes
4. Retrieve flat JSON data
5. Print a summary of what was returned

Prerequisites:
    Set these environment variables (or create a .env file):
    - PARTICLE_CLIENT_ID: Your Particle client ID
    - PARTICLE_CLIENT_SECRET: Your Particle client secret
    - PARTICLE_SCOPE_ID: Your Particle scope ID

    Validate your setup first:
        python workflows/check_setup.py

Usage:
    python workflows/hello_particle.py

Notes:
    - Uses sandbox environment by default
    - Uses a fixed patient_id for idempotent re-runs
    - Query polling may take 2-5 minutes
"""

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

DEMO_PATIENT = PatientRegistration(
    given_name="Elvira",
    family_name="Valadez-Nucleus",
    date_of_birth="1970-12-26",
    gender=Gender.FEMALE,
    postal_code="02215",
    address_city="Boston",
    address_state="Massachusetts",
    patient_id="hello-particle-demo",
    address_lines=[""],
    ssn="123-45-6789",
    telephone="234-567-8910",
)


def print_summary(data: dict) -> None:
    """Print a human-readable summary of flat data."""
    print("\n=== Data Summary ===\n")

    # Resource type counts
    print("Resource types returned:")
    for key, value in sorted(data.items()):
        if isinstance(value, list):
            print(f"  {key}: {len(value)} records")

    # Sample medications
    medications = data.get("medications", [])
    if medications:
        print(f"\nMedications ({len(medications)}):")
        for med in medications[:5]:
            name = med.get("medication_name", "Unknown")
            route = med.get("medication_statement_dose_route", "")
            print(f"  - {name}")
            if route:
                print(f"    Route: {route}")

    # Sample problems/conditions
    problems = data.get("problems", [])
    if problems:
        print(f"\nProblems/Conditions ({len(problems)}):")
        for prob in problems[:5]:
            name = prob.get("condition_name", "Unknown")
            status = prob.get("condition_clinical_status", "")
            onset = prob.get("condition_onset_date", "")
            print(f"  - {name} [{status}]")
            if onset:
                print(f"    Onset: {onset}")

    # Sample encounters
    encounters = data.get("encounters", [])
    if encounters:
        print(f"\nEncounters ({len(encounters)}):")
        for enc in encounters[:5]:
            enc_type = enc.get("encounter_type_name", "Unknown")
            start = enc.get("encounter_start_time", "")
            end = enc.get("encounter_end_time", "")
            print(f"  - {enc_type}")
            if start:
                period = f"{start}"
                if end:
                    period += f" to {end}"
                print(f"    Period: {period}")


def main() -> None:
    """Run the full hello-particle workflow."""
    configure_logging()

    print("=== Hello Particle ===\n")

    settings = ParticleSettings()
    print(f"API: {settings.base_url}\n")

    try:
        with ParticleHTTPClient(settings) as client:
            patient_svc = PatientService(client)
            query_svc = QueryService(client)

            # Step 1: Register patient
            print("1. Registering demo patient...")
            response = patient_svc.register(DEMO_PATIENT)
            patient_id = response.particle_patient_id
            print(f"   Patient ID: {patient_id}")

            # Step 2: Submit query
            print("\n2. Submitting clinical data query...")
            query_svc.submit_query(
                particle_patient_id=patient_id,
                purpose_of_use=PurposeOfUse.TREATMENT,
            )
            print("   Query submitted")

            # Step 3: Poll for completion
            print("\n3. Waiting for query to complete (this may take 2-5 minutes)...")
            result = query_svc.wait_for_query_complete(
                particle_patient_id=patient_id,
                timeout_seconds=300,
            )
            print(f"   Status: {result.query_status.value}")
            if result.files_available:
                print(f"   Files available: {result.files_available}")

            # Step 4: Retrieve flat data
            print("\n4. Retrieving flat data...")
            data = query_svc.get_flat(patient_id)

            # Step 5: Print summary
            print_summary(data)

            print("\n=== Done! ===")
            print("\nNext steps:")
            print(f"  python workflows/retrieve_data.py {patient_id} flat   # full flat data")
            print(f"  python workflows/retrieve_data.py {patient_id} ccda   # CCDA documents")

    except ParticleValidationError as e:
        print(f"\nValidation error: {e.message}")
        if e.errors:
            for error in e.errors:
                print(f"  - {error}")

    except ParticleQueryTimeoutError as e:
        print(f"\nQuery timed out: {e.message}")
        print("  The query is still running. Try retrieve_data.py in a few minutes:")
        print(f"  python workflows/retrieve_data.py {e.patient_id} flat")

    except ParticleQueryFailedError as e:
        print(f"\nQuery failed: {e.message}")
        if e.error_message:
            print(f"  Details: {e.error_message}")

    except ParticleAPIError as e:
        print(f"\nAPI error ({e.status_code}): {e.message}")
        if e.response_body:
            print(f"  Details: {e.response_body}")


if __name__ == "__main__":
    main()
