#!/usr/bin/env python3
"""Signal End-to-End: Full Signal lifecycle in one script.

This script runs the complete Particle Signal workflow:
1. Register a demo patient
2. Subscribe the patient to MONITORING
3. Trigger an ADMIT_TRANSITION_ALERT sandbox workflow
4. Retrieve flat transitions data
5. Print a summary of what was returned

Prerequisites:
    Set these environment variables (or create a .env file):
    - PARTICLE_CLIENT_ID: Your Particle client ID
    - PARTICLE_CLIENT_SECRET: Your Particle client secret
    - PARTICLE_SCOPE_ID: Your Particle scope ID
    - SIGNAL_CALLBACK_URL (optional): Webhook URL for notifications

    Validate your setup first:
        python workflows/check_setup.py

Usage:
    python workflows/signal_end_to_end.py
    python workflows/signal_end_to_end.py https://your-webhook.example.com/callback

Notes:
    - Uses sandbox environment by default
    - Uses a fixed patient_id for idempotent re-runs
    - This is the "hello world" of Particle Signal
"""

import os
import sys

from particle.core import (
    ParticleAPIError,
    ParticleHTTPClient,
    ParticleSettings,
    ParticleValidationError,
    configure_logging,
)
from particle.patient import Gender, PatientRegistration, PatientService
from particle.signal import SignalService, WorkflowType

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


def get_callback_url() -> str:
    """Get callback URL from env, CLI arg, or default."""
    if len(sys.argv) > 1:
        return sys.argv[1]
    return os.environ.get("SIGNAL_CALLBACK_URL", "https://example.com/webhook")


def print_transitions_summary(data: dict) -> None:
    """Print a human-readable summary of flat transitions data."""
    print("\n=== Transitions Data Summary ===\n")

    if not data:
        print("  No transitions data returned yet.")
        print("  (In sandbox, data may take a moment to appear after triggering.)")
        return

    print("Resource types returned:")
    for key, value in sorted(data.items()):
        if isinstance(value, list):
            print(f"  {key}: {len(value)} records")

    encounters = data.get("encounters", [])
    if encounters:
        print(f"\nEncounters ({len(encounters)}):")
        for enc in encounters[:5]:
            enc_type = enc.get("encounter_type_name", "Unknown")
            start = enc.get("encounter_start_time", "")
            print(f"  - {enc_type}")
            if start:
                print(f"    Start: {start}")


def main() -> None:
    """Run the full Signal end-to-end workflow."""
    configure_logging()

    callback_url = get_callback_url()

    print("=== Signal: End-to-End ===\n")

    settings = ParticleSettings()
    print(f"API: {settings.base_url}")
    print(f"Callback URL: {callback_url}\n")

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
                subscription_ids = [sub.id for sub in sub_response.subscriptions]
                for sub_id in subscription_ids:
                    print(f"   Subscription ID: {sub_id}")
            else:
                subscription_ids = []
                print("   Subscribed successfully")

            # Step 3: Trigger sandbox workflow
            print("\n3. Triggering ADMIT_TRANSITION_ALERT workflow...")
            trigger_result = signal_svc.trigger_sandbox_workflow(
                particle_patient_id=patient_id,
                workflow=WorkflowType.ADMIT_TRANSITION_ALERT,
                callback_url=callback_url,
            )
            print(f"   Workflow triggered: {trigger_result}")

            # Step 4: Retrieve flat transitions data
            print("\n4. Retrieving flat transitions data...")
            transitions_data = signal_svc.get_flat_transitions(patient_id)

            # Step 5: Print summary
            print_transitions_summary(transitions_data)

            # Final summary
            print("\n=== Summary ===")
            print(f"  Patient ID:       {patient_id}")
            print(f"  Subscriptions:    {len(subscription_ids)}")
            print(f"  Workflow:         ADMIT_TRANSITION_ALERT")
            print(f"  Callback URL:     {callback_url}")

            print("\n=== Done! ===")

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
