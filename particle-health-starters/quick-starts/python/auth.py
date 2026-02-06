#!/usr/bin/env python3
"""Get a JWT auth token from Particle Health API.

Requires:
    PARTICLE_CLIENT_ID, PARTICLE_CLIENT_SECRET, PARTICLE_SCOPE_ID

Usage:
    python quick-starts/python/auth.py
"""

import os

import httpx

BASE_URL = os.environ.get("PARTICLE_BASE_URL", "https://sandbox.particlehealth.com")

response = httpx.get(
    f"{BASE_URL}/auth",
    headers={
        "client-id": os.environ["PARTICLE_CLIENT_ID"],
        "client-secret": os.environ["PARTICLE_CLIENT_SECRET"],
        "scope": os.environ["PARTICLE_SCOPE_ID"],
        "accept": "text/plain",
    },
)
response.raise_for_status()

token = response.text.strip()
print(f"Token: {token[:20]}...")
print(f"\nExport for other scripts:")
print(f'export PARTICLE_TOKEN="{token}"')
