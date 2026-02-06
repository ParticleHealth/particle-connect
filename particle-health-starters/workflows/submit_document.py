#!/usr/bin/env python3
"""Example: Submit a document for a patient with Particle Health API.

This script demonstrates:
1. Loading configuration from environment variables
2. Creating a validated document submission request
3. Submitting the document via the Particle API
4. Handling the response

Prerequisites:
    Set these environment variables:
    - PARTICLE_CLIENT_ID: Your Particle client ID
    - PARTICLE_CLIENT_SECRET: Your Particle client secret
    - PARTICLE_SCOPE_ID: Your Particle scope ID

Usage:
    # Set environment variables first
    export PARTICLE_CLIENT_ID=your-client-id
    export PARTICLE_CLIENT_SECRET=your-secret
    export PARTICLE_SCOPE_ID=your-scope

    # Submit an XML (CCDA) document
    python workflows/submit_document.py <patient_id>

    # Submit a PDF document
    python workflows/submit_document.py <patient_id> pdf

Notes:
    - Uses sandbox environment by default (PARTICLE_BASE_URL)
    - Submits document metadata and file content via multipart upload
    - Document ID enables idempotent re-submission
"""

import sys

from particle.core import (
    ParticleSettings,
    ParticleHTTPClient,
    ParticleAPIError,
    ParticleNotFoundError,
    ParticleValidationError,
    configure_logging,
)
from particle.document import DocumentService, DocumentSubmission, MimeType


def main() -> None:
    """Run document submission example."""
    if len(sys.argv) < 2:
        print("Usage: python workflows/submit_document.py <patient_id> [xml|pdf]")
        print()
        print("Arguments:")
        print("  patient_id  Your external patient ID assigned during registration")
        print("  xml|pdf     Document type (default: xml)")
        sys.exit(1)

    patient_id = sys.argv[1]
    doc_type = sys.argv[2].lower() if len(sys.argv) > 2 else "xml"

    # Validate document type
    if doc_type not in ("xml", "pdf"):
        print(f"Error: Invalid document type '{doc_type}'. Use 'xml' or 'pdf'.")
        sys.exit(1)

    # Enable structured logging (optional, but helpful for debugging)
    configure_logging()

    # Load settings from environment variables
    settings = ParticleSettings()
    print(f"Using Particle API at: {settings.base_url}")

    # Create document submission based on type
    if doc_type == "xml":
        document = DocumentSubmission(
            patient_id=patient_id,
            document_id="example-ccda-001",
            title="clinical_summary.xml",
            mime_type=MimeType.XML,
            creation_time="2020-01-01T12:30:00Z",
            format_code="urn:ihe:pcc:xphr:2007",
            class_code="11369-6",
            type_code="11369-6",
            # Optional: service time range
            service_start_time="2020-01-01T00:00:00Z",
            service_stop_time="2020-01-04T00:00:00Z",
        )
        # Minimal valid CCDA stub for demonstration
        file_content = b'<?xml version="1.0" encoding="UTF-8"?><ClinicalDocument xmlns="urn:hl7-org:v3"><title>Clinical Summary</title></ClinicalDocument>'
        print("Submitting CCDA (XML) document...")
    else:
        document = DocumentSubmission(
            patient_id=patient_id,
            document_id="example-pdf-001",
            title="lab_results.pdf",
            mime_type=MimeType.PDF,
            creation_time="2020-01-01T12:30:00Z",
            format_code="urn:ihe:pcc:xphr:2007",
            class_code="11369-6",
            type_code="11369-6",
        )
        # Minimal PDF stub for demonstration
        file_content = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[]/Count 0>>endobj\nxref\n0 3\ntrailer<</Size 3/Root 1 0 R>>\nstartxref\n0\n%%EOF"
        print("Submitting PDF document...")

    print(f"  Document ID: {document.document_id}")
    print(f"  Title: {document.title}")
    print(f"  MIME Type: {document.mime_type.value}")

    # Submit document via API
    try:
        with ParticleHTTPClient(settings) as client:
            service = DocumentService(client)
            response = service.submit(document, file_content=file_content)

        # Success!
        print("\nDocument submitted successfully!")
        print(f"  Document ID: {response.document_id}")
        print(f"  Patient ID: {response.patient_id}")
        if response.status:
            print(f"  Status: {response.status}")

    except ParticleNotFoundError as e:
        print(f"\nNot found: {e.message}")
        print("  Ensure the patient_id is a valid Particle patient UUID.")
        sys.exit(1)

    except ParticleValidationError as e:
        # API rejected the data (e.g., invalid field format)
        print(f"\nValidation error: {e.message}")
        if e.errors:
            for error in e.errors:
                print(f"  - {error}")
        sys.exit(1)

    except ParticleAPIError as e:
        # Other API error
        print(f"\nAPI error ({e.status_code}): {e.message}")
        if e.response_body:
            print(f"  Details: {e.response_body}")
        sys.exit(1)


if __name__ == "__main__":
    main()
