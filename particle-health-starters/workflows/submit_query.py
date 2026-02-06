#!/usr/bin/env python3
"""Example: Submit a clinical data query for a registered patient.

This script demonstrates:
1. Submitting a query for patient clinical data
2. Polling for query completion with exponential backoff
3. Handling query status (COMPLETE, PARTIAL, FAILED, timeout)

Prerequisites:
    Set these environment variables:
    - PARTICLE_CLIENT_ID: Your Particle client ID
    - PARTICLE_CLIENT_SECRET: Your Particle client secret
    - PARTICLE_SCOPE_ID: Your Particle scope ID

    You must have a registered patient ID from:
    - Running register_patient.py, OR
    - Calling PatientService.register() directly

Usage:
    # Set environment variables first
    export PARTICLE_CLIENT_ID=your-client-id
    export PARTICLE_CLIENT_SECRET=your-secret
    export PARTICLE_SCOPE_ID=your-scope

    # Run with a Particle patient ID
    python workflows/submit_query.py <particle_patient_id>

    # Or with uv
    uv run workflows/submit_query.py <particle_patient_id>

Notes:
    - Uses sandbox environment by default (PARTICLE_BASE_URL)
    - Default timeout is 300 seconds (5 minutes)
    - PARTIAL status is treated as successful (some data available)
    - After success, use retrieve_data.py to get clinical data
"""

import sys

from particle.core import (
    ParticleSettings,
    ParticleHTTPClient,
    ParticleAPIError,
    ParticleQueryTimeoutError,
    ParticleQueryFailedError,
    configure_logging,
)
from particle.query import QueryService, PurposeOfUse


def main() -> None:
    """Run query submission example."""
    # Validate command line arguments
    if len(sys.argv) < 2:
        print("Usage: python workflows/submit_query.py <particle_patient_id>")
        print("\nExample:")
        print("  python workflows/submit_query.py 12345678-1234-1234-1234-123456789012")
        sys.exit(1)

    particle_patient_id = sys.argv[1]

    # Enable structured logging (optional, but helpful for debugging)
    configure_logging()

    # Load settings from environment variables
    settings = ParticleSettings()
    print(f"Using Particle API at: {settings.base_url}")

    try:
        with ParticleHTTPClient(settings) as client:
            service = QueryService(client)

            # Submit the query
            print(f"\nSubmitting query for patient: {particle_patient_id}")
            response = service.submit_query(
                particle_patient_id=particle_patient_id,
                purpose_of_use=PurposeOfUse.TREATMENT,
            )
            print(f"  Query accepted for patient: {response.particle_patient_id}")

            # Wait for completion with polling
            print("\nWaiting for query to complete...")
            print("  (This may take up to 5 minutes)")
            result = service.wait_for_query_complete(
                particle_patient_id=particle_patient_id,
                timeout_seconds=300,
            )

            # Success!
            print("\nQuery completed!")
            print(f"  Status: {result.query_status.value}")
            if result.files_available:
                print(f"  Files available: {result.files_available}")
            print(f"  Patient ID: {particle_patient_id}")
            print("\nNext steps:")
            print(f"  python workflows/retrieve_data.py {particle_patient_id} fhir")
            print(f"  python workflows/retrieve_data.py {particle_patient_id} flat")
            print(f"  python workflows/retrieve_data.py {particle_patient_id} ccda")

    except ParticleQueryTimeoutError as e:
        print(f"\nQuery timed out: {e.message}")
        print("  The query is still running on Particle's servers.")
        print("  Try again later or increase the timeout.")
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
