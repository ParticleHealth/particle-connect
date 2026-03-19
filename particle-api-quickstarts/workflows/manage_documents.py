#!/usr/bin/env python3
"""Example: Manage documents for a patient with Particle Health API.

This script demonstrates the full bi-directional document lifecycle:
1. Retrieve a submitted document's metadata (verify upload)
2. List all documents for a patient
3. Delete a document

Prerequisites:
    Set these environment variables:
    - PARTICLE_CLIENT_ID: Your Particle client ID
    - PARTICLE_CLIENT_SECRET: Your Particle client secret
    - PARTICLE_SCOPE_ID: Your Particle scope ID

Usage:
    # Retrieve a document by ID
    python workflows/manage_documents.py get <document_id>

    # List all documents for a patient
    python workflows/manage_documents.py list <patient_id>

    # Delete a document by ID
    python workflows/manage_documents.py delete <document_id>

Notes:
    - Uses sandbox environment by default (PARTICLE_BASE_URL)
    - document_id and patient_id are your external IDs (not Particle UUIDs)
    - Use GET after submission to verify a document was uploaded successfully
"""

import sys

from particle.core import (
    ParticleAPIError,
    ParticleHTTPClient,
    ParticleNotFoundError,
    ParticleSettings,
    configure_logging,
)
from particle.document import DocumentService


def main() -> None:
    """Run document management example."""
    if len(sys.argv) < 3:
        print("Usage: python workflows/manage_documents.py [get|list|delete] <id>")
        print()
        print("Actions:")
        print("  get <document_id>   Retrieve document metadata")
        print("  list <patient_id>   List all documents for a patient")
        print("  delete <document_id> Delete a document")
        sys.exit(1)

    action = sys.argv[1].lower()
    target_id = sys.argv[2]

    if action not in ("get", "list", "delete"):
        print(f"Error: Invalid action '{action}'. Use get, list, or delete.")
        sys.exit(1)

    configure_logging()
    settings = ParticleSettings()
    print(f"Using Particle API at: {settings.base_url}")

    try:
        with ParticleHTTPClient(settings) as client:
            service = DocumentService(client)

            if action == "get":
                print(f"\nRetrieving document: {target_id}")
                doc = service.get(target_id)
                print(f"  Document ID: {doc.document_id}")
                print(f"  Patient ID: {doc.patient_id}")
                print(f"  Type: {doc.type}")
                print(f"  Title: {doc.title}")
                print(f"  MIME Type: {doc.mime_type}")
                print(f"  Created: {doc.creation_time}")
                print(f"  Format Code: {doc.format_code}")
                print(f"  Class Code: {doc.class_code}")
                print(f"  Type Code: {doc.type_code}")

            elif action == "list":
                print(f"\nListing documents for patient: {target_id}")
                documents = service.list_by_patient(target_id)
                print(f"Found {len(documents)} document(s):")
                for doc in documents:
                    print(f"  - {doc.document_id}: {doc.title} ({doc.mime_type})")

            elif action == "delete":
                print(f"\nDeleting document: {target_id}")
                result = service.delete(target_id)
                print(f"Result: {result}")

    except ParticleNotFoundError as e:
        print(f"\nNot found: {e.message}")
        sys.exit(1)

    except ParticleAPIError as e:
        print(f"\nAPI error ({e.status_code}): {e.message}")
        if e.response_body:
            print(f"  Details: {e.response_body}")
        sys.exit(1)


if __name__ == "__main__":
    main()
