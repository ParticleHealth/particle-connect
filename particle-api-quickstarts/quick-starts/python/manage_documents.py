#!/usr/bin/env python3
"""Manage documents: retrieve, delete, or list documents for a patient.

Part of the bi-directional document lifecycle. After submitting a document,
use these operations to verify, list, or remove documents.

Requires:
    PARTICLE_CLIENT_ID, PARTICLE_CLIENT_SECRET, PARTICLE_SCOPE_ID

Usage:
    python quick-starts/python/manage_documents.py get <document_id>
    python quick-starts/python/manage_documents.py delete <document_id>
    python quick-starts/python/manage_documents.py list <patient_id>
"""

import json
import os
import sys

import httpx

BASE_URL = os.environ.get("PARTICLE_BASE_URL", "https://sandbox.particlehealth.com")

if len(sys.argv) < 3:
    sys.exit(
        "Usage: python quick-starts/python/manage_documents.py"
        " [get|delete|list] <id>"
    )

action = sys.argv[1].lower()
target_id = sys.argv[2]

if action not in ("get", "delete", "list"):
    sys.exit(f"Invalid action: {action} (use get, delete, or list)")

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
headers = {"Authorization": f"Bearer {token}"}

# Step 2: Execute document operation
if action == "get":
    print(f"Retrieving document: {target_id}")
    response = httpx.get(
        f"{BASE_URL}/api/v1/documents/{target_id}",
        headers=headers,
    )
    response.raise_for_status()
    print(json.dumps(response.json(), indent=2))

elif action == "delete":
    print(f"Deleting document: {target_id}")
    response = httpx.delete(
        f"{BASE_URL}/api/v1/documents/{target_id}",
        headers=headers,
    )
    response.raise_for_status()
    print(f"Result: {response.text}")

elif action == "list":
    print(f"Listing documents for patient: {target_id}")
    response = httpx.get(
        f"{BASE_URL}/api/v1/documents/patient/{target_id}",
        headers=headers,
    )
    response.raise_for_status()
    documents = response.json()
    print(f"Found {len(documents)} document(s):")
    print(json.dumps(documents, indent=2))
