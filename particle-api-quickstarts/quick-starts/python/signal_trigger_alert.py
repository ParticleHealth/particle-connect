#!/usr/bin/env python3
"""Subscribe a patient and trigger a sandbox alert workflow.

Requires:
    PARTICLE_CLIENT_ID, PARTICLE_CLIENT_SECRET, PARTICLE_SCOPE_ID

Usage:
    python quick-starts/python/signal_trigger_alert.py
"""

import json
import os

import httpx

BASE_URL = os.environ.get("PARTICLE_BASE_URL", "https://sandbox.particlehealth.com")

# Step 1: Get auth token
token_response = httpx.get(
    f"{BASE_URL}/auth",
    headers={
        "client-id": os.environ["PARTICLE_CLIENT_ID"],
        "client-secret": os.environ["PARTICLE_CLIENT_SECRET"],
        "scope": os.environ["PARTICLE_SCOPE_ID"],
        "accept": "text/plain",
    },
)
token_response.raise_for_status()
token = token_response.text.strip()
headers = {"Authorization": f"Bearer {token}", "accept": "application/json"}

# Step 2: Register test patient
print("Registering test patient...")
patient_response = httpx.post(
    f"{BASE_URL}/api/v2/patients",
    headers={**headers, "content-type": "application/json"},
    json={
        "given_name": "Elvira",
        "family_name": "Valadez-Nucleus",
        "date_of_birth": "1970-12-26",
        "gender": "FEMALE",
        "address_city": "Boston",
        "address_state": "MA",
        "postal_code": "02215",
        "patient_id": "signal-quickstart-demo",
    },
)
patient_response.raise_for_status()
patient_data = patient_response.json()
particle_patient_id = patient_data["particle_patient_id"]
print(f"Particle Patient ID: {particle_patient_id}")

# Step 3: Subscribe to monitoring
print("\nSubscribing patient to MONITORING...")
sub_response = httpx.post(
    f"{BASE_URL}/api/v1/patients/{particle_patient_id}/subscriptions",
    headers={**headers, "content-type": "application/json"},
    json={"subscriptions": [{"type": "MONITORING"}]},
)
if sub_response.status_code == 400:
    print("Already subscribed")
else:
    sub_response.raise_for_status()
    print("Subscribed successfully" if not sub_response.content else sub_response.text)

# Step 4: Trigger sandbox workflow
print("\nTriggering sandbox alert workflow...")
response = httpx.post(
    f"{BASE_URL}/api/v1/patients/{particle_patient_id}/subscriptions/trigger-sandbox-workflow",
    headers={**headers, "content-type": "application/json"},
    json={
        "workflow": "ADMIT_TRANSITION_ALERT",
        "callback_url": "https://example.com/webhook",
        "display_name": "Test Admit Alert",
    },
)
response.raise_for_status()
print(f"Trigger response: {response.text}")
