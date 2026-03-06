#!/usr/bin/env python3
"""Signal Trigger Alert: Register, subscribe, and trigger a sandbox alert.

This script demonstrates triggering a Signal workflow in sandbox:
1. Register a demo patient
2. Subscribe the patient to MONITORING
3. Trigger an ADMIT_TRANSITION_ALERT sandbox workflow

Prerequisites:
    Set these environment variables (or create a .env file):
    - PARTICLE_CLIENT_ID: Your Particle client ID
    - PARTICLE_CLIENT_SECRET: Your Particle client secret
    - PARTICLE_SCOPE_ID: Your Particle scope ID
    - SIGNAL_CALLBACK_URL (optional): Webhook URL for notifications

    Validate your setup first:
        python workflows/check_setup.py

Usage:
    python workflows/signal_trigger_alert.py
    python workflows/signal_trigger_alert.py https://your-webhook.example.com/callback

Notes:
    - Uses sandbox environment by default
    - Uses a fixed patient_id for idempotent re-runs
    - The callback_url receives CloudEvents webhook notifications
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


def main() -> None:
    """Register a patient, subscribe, and trigger an alert."""
    configure_logging()

    callback_url = get_callback_url()

    print("=== Signal: Trigger Alert ===\n")

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
                for sub in sub_response.subscriptions:
                    print(f"   Subscription ID: {sub.id}")
            else:
                print("   Subscribed successfully")

            # Step 3: Trigger sandbox workflow
            # Using ADMIT_TRANSITION_ALERT here. Other workflow types you can try:
            #   WorkflowType.DISCHARGE_TRANSITION_ALERT  - hospital discharge
            #   WorkflowType.TRANSFER_TRANSITION_ALERT   - hospital transfer
            #   WorkflowType.NEW_ENCOUNTER_ALERT         - new encounter
            #   WorkflowType.REFERRAL_ALERT              - referral
            #   WorkflowType.DISCHARGE_SUMMARY_ALERT     - discharge summary
            #   WorkflowType.ADT                         - raw ADT (requires event_type)
            print("\n3. Triggering ADMIT_TRANSITION_ALERT workflow...")
            result = signal_svc.trigger_sandbox_workflow(
                particle_patient_id=patient_id,
                workflow=WorkflowType.ADMIT_TRANSITION_ALERT,
                callback_url=callback_url,
            )
            print(f"   Workflow triggered: {result}")

            print("\n=== Done! ===")
            print(f"\nParticle will send a webhook notification to: {callback_url}")
            print("\nNext steps:")
            print("  python workflows/signal_end_to_end.py   # full Signal lifecycle")

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
