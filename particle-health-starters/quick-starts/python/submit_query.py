#!/usr/bin/env python3
"""Submit a clinical data query for a patient.

Requires:
    PARTICLE_CLIENT_ID, PARTICLE_CLIENT_SECRET, PARTICLE_SCOPE_ID

Usage:
    python quick-starts/python/submit_query.py <particle_patient_id>
"""

import json
import os
import sys
import time

import httpx

BASE_URL = os.environ.get("PARTICLE_BASE_URL", "https://sandbox.particlehealth.com")

patient_id = sys.argv[1] if len(sys.argv) > 1 else sys.exit(
    "Usage: python quick-starts/python/submit_query.py <particle_patient_id>"
)

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

# Step 2: Submit query
print(f"Submitting query for patient: {patient_id}")
response = httpx.post(
    f"{BASE_URL}/api/v2/patients/{patient_id}/query",
    headers={**headers, "content-type": "application/json"},
    json={"purpose_of_use": "TREATMENT"},
)
response.raise_for_status()
print(json.dumps(response.json(), indent=2))

# Step 3: Poll for completion
print("\nPolling for query completion...")
for i in range(30):
    time.sleep(10)
    status_response = httpx.get(
        f"{BASE_URL}/api/v2/patients/{patient_id}/query",
        headers=headers,
    )
    status_response.raise_for_status()
    status = status_response.json()
    query_status = status.get("query_status", "UNKNOWN")
    print(f"  [{i+1}] Status: {query_status}")

    if query_status in ("COMPLETE", "PARTIAL"):
        print("\nQuery complete!")
        print(json.dumps(status, indent=2))
        break
    elif query_status == "FAILED":
        print("\nQuery failed!")
        print(json.dumps(status, indent=2))
        sys.exit(1)
else:
    print("\nTimed out waiting for query to complete.")
    sys.exit(1)
