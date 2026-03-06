#!/usr/bin/env python3
"""Register an organization for Signal referral alerts.

Requires:
    PARTICLE_CLIENT_ID, PARTICLE_CLIENT_SECRET, PARTICLE_SCOPE_ID

Usage:
    python quick-starts/python/signal_register_org.py
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

# Step 2: Register organization (Rochester Hospital sandbox org)
print("Registering organization...")
response = httpx.post(
    f"{BASE_URL}/api/v1/referrals/organizations/registered",
    headers={**headers, "content-type": "application/json"},
    json={
        "organizations": [
            {"oid": "2.16.840.1.113883.3.8391.5.710576"},
        ],
    },
)
response.raise_for_status()
print(json.dumps(response.json(), indent=2))
