#!/usr/bin/env python3
"""Register a patient with Particle Health API.

Requires:
    PARTICLE_CLIENT_ID, PARTICLE_CLIENT_SECRET, PARTICLE_SCOPE_ID

Usage:
    python quick-starts/python/register_patient.py
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

# Step 2: Register patient
response = httpx.post(
    f"{BASE_URL}/api/v2/patients",
    headers={
        "Authorization": f"Bearer {token}",
        "content-type": "application/json",
        "accept": "application/json",
    },
    json={
        "given_name": "Kam",
        "family_name": "Quark",
        "date_of_birth": "1954-12-01",
        "gender": "MALE",
        "postal_code": "11111",
        "address_city": "Brooklyn",
        "address_state": "New York",
        "address_lines": ["999 Dev Drive"],
        "ssn": "123-45-6789",
        "telephone": "234-567-8910",
        "patient_id": "my-external-id",
    },
)
response.raise_for_status()

data = response.json()
print(json.dumps(data, indent=2))
print(f"\nParticle Patient ID: {data['id']}")
