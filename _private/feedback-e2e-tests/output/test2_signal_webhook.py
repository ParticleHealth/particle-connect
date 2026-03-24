#!/usr/bin/env python3
"""Signal Webhook E2E Test: Register, subscribe, trigger, and receive alerts.

This script demonstrates the full Particle Signal webhook lifecycle:
1. Register the sandbox test patient
2. Subscribe the patient to MONITORING
3. Start a local FastAPI webhook receiver on port 8080
4. Trigger an ADMIT_TRANSITION_ALERT via the sandbox trigger endpoint
5. Receive the CloudEvents webhook, verify the HMAC signature, parse the payload
6. Print the parsed alert details (event type, patient, facility, timestamp)

Prerequisites:
    Set these environment variables (or create a .env file in particle-api-quickstarts/):
    - PARTICLE_CLIENT_ID
    - PARTICLE_CLIENT_SECRET
    - PARTICLE_SCOPE_ID

    Expose port 8080 publicly via ngrok or similar:
        ngrok http 8080
    Then set the SIGNAL_CALLBACK_URL env var to the ngrok HTTPS URL + /webhook.

Usage:
    python _private/feedback-e2e-tests/output/test2_signal_webhook.py

    # Or with an explicit callback URL:
    SIGNAL_CALLBACK_URL=https://abc123.ngrok.io/webhook python test2_signal_webhook.py
"""

import hashlib
import hmac
import json
import os
import sys
import threading
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import uvicorn
from fastapi import FastAPI, Header, Request, Response

# ---------------------------------------------------------------------------
# Ensure the particle SDK is importable when running from repo root
# ---------------------------------------------------------------------------
_REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
for _ in range(4):  # walk up to repo root
    _REPO_ROOT = os.path.dirname(_REPO_ROOT)
_SDK_SRC = os.path.join(_REPO_ROOT, "particle-api-quickstarts", "src")
if _SDK_SRC not in sys.path:
    sys.path.insert(0, _SDK_SRC)

from particle.core import (
    ParticleAPIError,
    ParticleHTTPClient,
    ParticleSettings,
    ParticleValidationError,
    configure_logging,
)
from particle.patient import Gender, PatientRegistration, PatientService
from particle.signal import SignalService, WorkflowType

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
WEBHOOK_PORT = int(os.environ.get("WEBHOOK_PORT", "8080"))
WEBHOOK_PATH = "/webhook"

# The HMAC signing key — in production this comes from your Particle project
# settings.  For sandbox testing it may not be configured; set this env var
# if you have one so the script can verify signatures.
WEBHOOK_SIGNING_KEY = os.environ.get("WEBHOOK_SIGNING_KEY", "")

# Sandbox test patient (same demographics as the seeded patient)
DEMO_PATIENT = PatientRegistration(
    given_name="Elvira",
    family_name="Valadez-Nucleus",
    date_of_birth="1970-12-26",
    gender=Gender.FEMALE,
    postal_code="02215",
    address_city="Boston",
    address_state="MA",  # MUST be two-letter abbreviation
    patient_id="signal-webhook-e2e-test",
    address_lines=[""],
    ssn="123-45-6789",
    telephone="234-567-8910",
)

# ---------------------------------------------------------------------------
# Threading event so the main thread knows when a webhook has been received
# ---------------------------------------------------------------------------
webhook_received = threading.Event()
received_payload: dict = {}


# ---------------------------------------------------------------------------
# HMAC signature verification
# ---------------------------------------------------------------------------
def verify_hmac_signature(
    raw_body: bytes,
    signature_header: str | None,
    signing_key: str,
) -> bool:
    """Verify the X-Ph-Signature-256 HMAC signature on a webhook request.

    Header format:  t={unix_timestamp},{hmac_hex_signature}
    Signed payload: {timestamp}.{raw_json_body}

    Args:
        raw_body: The raw request body bytes.
        signature_header: Value of the X-Ph-Signature-256 header.
        signing_key: Your HMAC signing key from Particle.

    Returns:
        True if the signature is valid, False otherwise.
    """
    if not signature_header or not signing_key:
        return False

    try:
        # Parse "t={timestamp},{signature}"
        parts = signature_header.split(",", 1)
        if len(parts) != 2:
            return False

        timestamp_part = parts[0]  # "t=1234567890"
        received_sig = parts[1]

        if not timestamp_part.startswith("t="):
            return False

        timestamp = timestamp_part[2:]  # strip "t="

        # Construct signed payload: "{timestamp}.{raw_body}"
        signed_payload = f"{timestamp}.".encode() + raw_body

        # Compute expected HMAC SHA-256
        expected_sig = hmac.new(
            signing_key.encode(),
            signed_payload,
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(expected_sig, received_sig)
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Parse and print a CloudEvents webhook notification
# ---------------------------------------------------------------------------
def print_alert_details(payload: dict) -> None:
    """Parse a CloudEvents payload using the SDK and print alert details."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Use the SDK's static parser for validation
    notification = SignalService.parse_webhook_notification(payload)

    data = payload.get("data", {})

    # Extract details
    cloud_event_type = notification.type
    subject = notification.subject or "unknown"
    event_id = notification.id
    event_time = str(notification.time) if notification.time else "unknown"
    alert_event_type = data.get("event_type", subject)
    patient_id = data.get("particle_patient_id", "unknown")
    external_patient_id = data.get("external_patient_id", "unknown")
    network_org = data.get("network_organization", {})
    facility_name = network_org.get("name", "") if network_org else ""
    facility_oid = network_org.get("oid", "") if network_org else ""
    event_sequence = data.get("event_sequence", "unknown")
    is_final = data.get("is_final_event", "unknown")
    resources = data.get("resources", [])

    print(f"\n{'=' * 65}")
    print(f"  WEBHOOK RECEIVED at {now}")
    print(f"{'=' * 65}")
    print(f"  CloudEvent Type : {cloud_event_type}")
    print(f"  Subject         : {subject}")
    print(f"  Event ID        : {event_id}")
    print(f"  Event Time      : {event_time}")
    print(f"  Alert Type      : {alert_event_type}")
    print(f"  Patient ID      : {patient_id}")
    print(f"  External ID     : {external_patient_id}")
    print(f"  Facility Name   : {facility_name or '(empty)'}")
    print(f"  Facility OID    : {facility_oid or '(empty)'}")
    print(f"  Event Sequence  : {event_sequence}")
    print(f"  Is Final Event  : {is_final}")

    if resources:
        print(f"  Resources       :")
        for res in resources:
            file_id = res.get("file_id", "")
            resource_ids = res.get("resource_ids", [])
            print(f"    file_id      : {file_id or '(empty)'}")
            print(f"    resource_ids : {resource_ids}")

    print(f"{'=' * 65}\n")


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Signal that the server is ready."""
    print(f"\nWebhook receiver listening on http://localhost:{WEBHOOK_PORT}{WEBHOOK_PATH}")
    yield

app = FastAPI(title="Signal Webhook Receiver", lifespan=lifespan)


@app.post(WEBHOOK_PATH)
async def receive_webhook(
    request: Request,
    x_ph_signature_256: str | None = Header(None),
) -> Response:
    """Receive and process a CloudEvents webhook from Particle Health."""
    global received_payload

    raw_body = await request.body()

    # Verify HMAC signature if a signing key is configured
    if WEBHOOK_SIGNING_KEY:
        if verify_hmac_signature(raw_body, x_ph_signature_256, WEBHOOK_SIGNING_KEY):
            print("[HMAC] Signature verified OK")
        else:
            print("[HMAC] WARNING: Signature verification FAILED")
    else:
        if x_ph_signature_256:
            print("[HMAC] Signature header present but no WEBHOOK_SIGNING_KEY configured — skipping verification")
        else:
            print("[HMAC] No signature header and no signing key configured")

    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        print("[WARN] Received invalid JSON body")
        return Response(status_code=400, content="Invalid JSON")

    received_payload = payload
    print_alert_details(payload)

    # Signal to the main thread that a webhook has arrived
    webhook_received.set()

    return Response(
        status_code=200,
        content=json.dumps({"status": "ok"}),
        media_type="application/json",
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# ---------------------------------------------------------------------------
# Run the FastAPI server in a background thread
# ---------------------------------------------------------------------------
def start_webhook_server() -> threading.Thread:
    """Start the FastAPI webhook server in a daemon thread."""
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=WEBHOOK_PORT,
        log_level="warning",
    )
    server = uvicorn.Server(config)

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    # Give the server a moment to bind
    time.sleep(1)
    return thread


# ---------------------------------------------------------------------------
# Main workflow
# ---------------------------------------------------------------------------
def get_callback_url() -> str:
    """Get callback URL from env or fall back to localhost."""
    url = os.environ.get("SIGNAL_CALLBACK_URL", "")
    if url:
        return url
    # Default to localhost — works only if Particle can reach it
    # (e.g., via ngrok tunnel)
    return f"http://localhost:{WEBHOOK_PORT}{WEBHOOK_PATH}"


def main() -> None:
    """Run the full Signal webhook end-to-end workflow."""
    configure_logging()

    callback_url = get_callback_url()

    print("=" * 65)
    print("  Signal Webhook E2E Test")
    print("=" * 65)

    settings = ParticleSettings()
    print(f"\nAPI Base URL  : {settings.base_url}")
    print(f"Callback URL  : {callback_url}")
    print(f"Webhook Port  : {WEBHOOK_PORT}")

    if "localhost" in callback_url or "127.0.0.1" in callback_url:
        print(
            "\n  NOTE: Using localhost callback. Particle cannot reach localhost"
            "\n  directly. Use ngrok or a similar tunnel and set SIGNAL_CALLBACK_URL."
            "\n  The sandbox trigger will still return 'success' but the webhook"
            "\n  delivery may not arrive.\n"
        )

    try:
        with ParticleHTTPClient(settings) as client:
            patient_svc = PatientService(client)
            signal_svc = SignalService(client)

            # Step 1: Register patient
            print("\n--- Step 1: Register sandbox test patient ---")
            response = patient_svc.register(DEMO_PATIENT)
            patient_id = response.particle_patient_id
            print(f"  Particle Patient ID: {patient_id}")

            # Step 2: Subscribe to MONITORING
            print("\n--- Step 2: Subscribe patient to MONITORING ---")
            sub_response = signal_svc.subscribe(particle_patient_id=patient_id)
            if sub_response.subscriptions:
                for sub in sub_response.subscriptions:
                    print(f"  Subscription ID: {sub.id} (type: {sub.type})")
            else:
                print("  Subscribed (already subscribed or empty response)")

            # Step 3: Start the webhook receiver
            print("\n--- Step 3: Start FastAPI webhook receiver ---")
            server_thread = start_webhook_server()
            print(f"  Server running on port {WEBHOOK_PORT}")

            # Step 4: Trigger ADMIT_TRANSITION_ALERT
            print("\n--- Step 4: Trigger ADMIT_TRANSITION_ALERT ---")
            trigger_result = signal_svc.trigger_sandbox_workflow(
                particle_patient_id=patient_id,
                workflow=WorkflowType.ADMIT_TRANSITION_ALERT,
                callback_url=callback_url,
            )
            # trigger_sandbox_workflow returns plain text "success", not JSON
            print(f"  Trigger result: {trigger_result}")

            # Step 5: Wait for webhook delivery
            print("\n--- Step 5: Waiting for webhook (up to 30 seconds) ---")
            arrived = webhook_received.wait(timeout=30)
            if arrived:
                print("  Webhook received and processed (see details above).")
            else:
                print("  No webhook received within 30 seconds.")
                print("  This is expected if using a localhost callback without a tunnel.")
                print("  In a real setup, use ngrok and set SIGNAL_CALLBACK_URL.")

            # Final summary
            print(f"\n{'=' * 65}")
            print("  SUMMARY")
            print(f"{'=' * 65}")
            print(f"  Patient ID          : {patient_id}")
            print(f"  Workflow Triggered   : ADMIT_TRANSITION_ALERT")
            print(f"  Callback URL        : {callback_url}")
            print(f"  Webhook Received    : {'Yes' if arrived else 'No'}")
            print(f"{'=' * 65}\n")

    except ParticleValidationError as e:
        print(f"\nValidation error: {e.message}")
        if e.errors:
            for error in e.errors:
                print(f"  - {error}")
        sys.exit(1)

    except ParticleAPIError as e:
        print(f"\nAPI error ({e.status_code}): {e.message}")
        if e.response_body:
            print(f"  Details: {e.response_body}")
        sys.exit(1)


if __name__ == "__main__":
    main()
