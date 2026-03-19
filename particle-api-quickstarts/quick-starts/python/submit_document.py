#!/usr/bin/env python3
"""Submit a clinical document (CCDA XML or PDF) for a patient.

This is the bi-directional flow: sending clinical data BACK to Particle
for contribution to the health information exchange network.

Requires:
    PARTICLE_CLIENT_ID, PARTICLE_CLIENT_SECRET, PARTICLE_SCOPE_ID

Usage:
    python quick-starts/python/submit_document.py <patient_id> [xml|pdf]

Note: patient_id is your EXTERNAL patient ID (not the Particle UUID).
"""

import json
import os
import sys

import httpx

BASE_URL = os.environ.get("PARTICLE_BASE_URL", "https://sandbox.particlehealth.com")

if len(sys.argv) < 2:
    sys.exit(
        "Usage: python quick-starts/python/submit_document.py"
        " <patient_id> [xml|pdf]"
    )

patient_id = sys.argv[1]
doc_type = sys.argv[2].lower() if len(sys.argv) > 2 else "xml"

if doc_type not in ("xml", "pdf"):
    sys.exit(f"Invalid document type: {doc_type} (use xml or pdf)")

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

# Step 2: Build document metadata and file content
if doc_type == "xml":
    metadata = {
        "patient_id": patient_id,
        "document_id": "example-ccda-001",
        "type": "CLINICAL",
        "title": "clinical_summary.xml",
        "mime_type": "application/xml",
        "creation_time": "2020-01-01T12:30:00Z",
        "format_code": "urn:ihe:pcc:xphr:2007",
        "confidentiality_code": "N",
        "class_code": "11369-6",
        "type_code": "11369-6",
        "healthcare_facility_type_code": "394777002",
        "practice_setting_code": "394733009",
        "service_start_time": "2020-01-01T00:00:00Z",
        "service_stop_time": "2020-01-04T00:00:00Z",
    }
    file_content = (
        b'<?xml version="1.0" encoding="UTF-8"?>'
        b'<ClinicalDocument xmlns="urn:hl7-org:v3">'
        b"<title>Clinical Summary</title>"
        b"</ClinicalDocument>"
    )
    file_name = "clinical_summary.xml"
    mime_type = "application/xml"
    print("Submitting CCDA (XML) document...")
else:
    metadata = {
        "patient_id": patient_id,
        "document_id": "example-pdf-001",
        "type": "CLINICAL",
        "title": "lab_results.pdf",
        "mime_type": "application/pdf",
        "creation_time": "2020-01-01T12:30:00Z",
        "format_code": "urn:ihe:pcc:xphr:2007",
        "class_code": "11369-6",
        "type_code": "11369-6",
    }
    file_content = (
        b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[]/Count 0>>endobj\n"
        b"xref\n0 3\ntrailer<</Size 3/Root 1 0 R>>\n"
        b"startxref\n0\n%%EOF"
    )
    file_name = "lab_results.pdf"
    mime_type = "application/pdf"
    print("Submitting PDF document...")

print(f"  Patient ID: {patient_id}")
print(f"  Document ID: {metadata['document_id']}")

# Step 3: Submit via multipart upload
response = httpx.post(
    f"{BASE_URL}/api/v1/documents",
    headers=headers,
    files={
        "metadata": (None, json.dumps(metadata), "application/json"),
        "file": (file_name, file_content, mime_type),
    },
)
response.raise_for_status()

print("\nDocument submitted successfully!")
print(json.dumps(response.json(), indent=2))
