#!/usr/bin/env python3
"""Signal Subscribe Patient: Register and subscribe a patient to monitoring.

This script demonstrates the first step of Particle Signal:
1. Register a demo patient
2. Subscribe the patient to MONITORING

Prerequisites:
    Set these environment variables (or create a .env file):
    - PARTICLE_CLIENT_ID: Your Particle client ID
    - PARTICLE_CLIENT_SECRET: Your Particle client secret
    - PARTICLE_SCOPE_ID: Your Particle scope ID

    Validate your setup first:
        python workflows/check_setup.py

Usage:
    python workflows/signal_subscribe_patient.py

Notes:
    - Uses sandbox environment by default
    - Uses a fixed patient_id for idempotent re-runs
"""

from particle.core import (
    ParticleAPIError,
    ParticleHTTPClient,
    ParticleSettings,
    ParticleValidationError,
    configure_logging,
)
from particle.patient import Gender, PatientRegistration, PatientService
from particle.signal import SignalService

DEMO_PATIENT = PatientRegistration(
    given_name="Elvira",
    family_name="Valadez-Nucleus",
    date_of_birth="1970-12-26",
    gender=Gender.FEMALE,
    postal_code="02215",
    address_city="Boston",
    address_state="MA",
    patient_id="signal-demo-patient",
    address_lines=[""],
    ssn="123-45-6789",
    telephone="234-567-8910",
)


def main() -> None:
    """Register a patient and subscribe to monitoring."""
    configure_logging()

    print("=== Signal: Subscribe Patient ===\n")

    settings = ParticleSettings()
    print(f"API: {settings.base_url}\n")

    try:
        with ParticleHTTPClient(settings) as client:
            patient_svc = PatientService(client)
            signal_svc = SignalService(client)

            # Step 1: Register patient
            print("1. Registering demo patient...")
            response = patient_svc.register(DEMO_PATIENT)
            patient_id = response.particle_patient_id
            print(f"   Patient ID: {patient_id}")

            # Step 2: Subscribe to monitoring
            print("\n2. Subscribing patient to MONITORING...")
            sub_response = signal_svc.subscribe(particle_patient_id=patient_id)
            if sub_response.subscriptions:
                for sub in sub_response.subscriptions:
                    print(f"   Subscription ID: {sub.id}")
                    print(f"   Subscription Type: {sub.type.value}")
            else:
                print("   Subscribed successfully")

            print("\n=== Done! ===")
            print("\nNext steps:")
            print("  python workflows/signal_trigger_alert.py   # trigger a sandbox alert")
            print("  python workflows/signal_end_to_end.py      # full Signal lifecycle")

    except ParticleValidationError as e:
        print(f"\nValidation error: {e.message}")
        if e.errors:
            for error in e.errors:
                print(f"  - {error}")

    except ParticleAPIError as e:
        print(f"\nAPI error ({e.status_code}): {e.message}")
        if e.response_body:
            print(f"  Details: {e.response_body}")


if __name__ == "__main__":
    main()
