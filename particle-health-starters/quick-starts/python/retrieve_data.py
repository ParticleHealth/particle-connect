#!/usr/bin/env python3
"""Retrieve clinical data for a patient.

Requires:
    PARTICLE_CLIENT_ID, PARTICLE_CLIENT_SECRET, PARTICLE_SCOPE_ID

Usage:
    python quick-starts/python/retrieve_data.py <particle_patient_id> [flat|fhir|ccda]
"""

import json
import os
import sys

import httpx

BASE_URL = os.environ.get("PARTICLE_BASE_URL", "https://sandbox.particlehealth.com")

if len(sys.argv) < 2:
    sys.exit(
        "Usage: python quick-starts/python/retrieve_data.py"
        " <particle_patient_id> [flat|fhir|ccda]"
    )

patient_id = sys.argv[1]
data_format = sys.argv[2] if len(sys.argv) > 2 else "flat"

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

# Step 2: Retrieve data
print(f"Retrieving {data_format} data for patient: {patient_id}")

if data_format in ("flat", "fhir"):
    response = httpx.get(
        f"{BASE_URL}/api/v2/patients/{patient_id}/{data_format}",
        headers=headers,
    )
    response.raise_for_status()
    print(json.dumps(response.json(), indent=2))

elif data_format == "ccda":
    response = httpx.get(
        f"{BASE_URL}/api/v2/patients/{patient_id}/ccda",
        headers=headers,
    )
    response.raise_for_status()
    with open("ccda_data.zip", "wb") as f:
        f.write(response.content)
    print(f"Saved to ccda_data.zip ({len(response.content):,} bytes)")

else:
    sys.exit(f"Invalid format: {data_format} (use flat, fhir, or ccda)")
