#!/usr/bin/env python3
"""Bi-directional document submission round-trip test.

Tests the full Documents API lifecycle:
1. Authenticate with the sandbox API
2. Submit a minimal C-CDA XML document via POST /api/v1/documents
3. List documents for the patient to confirm submission
4. Retrieve the submitted document metadata
5. Compare submitted vs retrieved metadata and print a diff summary
6. Clean up by deleting the test document

Prerequisites:
    Set these environment variables (or create a .env file in particle-api-quickstarts/):
    - PARTICLE_CLIENT_ID: Your Particle client ID
    - PARTICLE_CLIENT_SECRET: Your Particle client secret
    - PARTICLE_SCOPE_ID: Your Particle scope ID

Usage:
    cd particle-api-quickstarts
    source .venv/bin/activate
    python ../_private/feedback-e2e-tests/output/test3_bidirectional.py

Notes:
    - Uses the Documents API v1 endpoints (not v2)
    - patient_id is the external ID assigned during registration (not the Particle UUID)
    - The patient must already exist in Particle's Master Patient Index
    - Submitting the same document_id again is an idempotent update
    - List returns null (not []) when no documents exist -- SDK handles this
"""

import sys
import uuid
from datetime import datetime, timezone

from particle.core import (
    ParticleAPIError,
    ParticleAuthError,
    ParticleHTTPClient,
    ParticleNotFoundError,
    ParticleSettings,
    ParticleValidationError,
    configure_logging,
)
from particle.document import DocumentService, DocumentSubmission, MimeType
from particle.patient import Gender, PatientRegistration, PatientService

# ---------------------------------------------------------------------------
# Test constants
# ---------------------------------------------------------------------------

# Use the seeded demo patient that works in sandbox
DEMO_PATIENT = PatientRegistration(
    given_name="Elvira",
    family_name="Valadez-Nucleus",
    date_of_birth="1970-12-26",
    gender=Gender.FEMALE,
    postal_code="02215",
    address_city="Boston",
    address_state="MA",  # Two-letter abbreviation required
    patient_id="bidir-test-patient",
    address_lines=[""],
    ssn="123-45-6789",
    telephone="234-567-8910",
)

# Unique document ID per run to avoid collisions
TEST_DOCUMENT_ID = f"bidir-test-{uuid.uuid4().hex[:8]}"

# Minimal valid C-CDA XML document
CCDA_XML = (
    b'<?xml version="1.0" encoding="UTF-8"?>\n'
    b'<ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n'
    b"  <realmCode code=\"US\"/>\n"
    b'  <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>\n'
    b"  <id root=\"2.16.840.1.113883.19\" extension=\"bidir-test\"/>\n"
    b'  <code code="34133-9" codeSystem="2.16.840.1.113883.6.1" displayName="Summarization of Episode Note"/>\n'
    b"  <title>Bi-Directional Test Document</title>\n"
    b"  <effectiveTime value=\"20200101123000\"/>\n"
    b'  <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>\n'
    b'  <languageCode code="en-US"/>\n'
    b"  <recordTarget>\n"
    b"    <patientRole>\n"
    b"      <id root=\"2.16.840.1.113883.19.5\" extension=\"bidir-test-patient\"/>\n"
    b"      <patient>\n"
    b"        <name><given>Elvira</given><family>Valadez-Nucleus</family></name>\n"
    b"        <administrativeGenderCode code=\"F\" codeSystem=\"2.16.840.1.113883.5.1\"/>\n"
    b"        <birthTime value=\"19701226\"/>\n"
    b"      </patient>\n"
    b"    </patientRole>\n"
    b"  </recordTarget>\n"
    b"  <component>\n"
    b"    <structuredBody>\n"
    b"      <component>\n"
    b"        <section>\n"
    b"          <title>Reason for Visit</title>\n"
    b"          <text>Bi-directional round-trip test.</text>\n"
    b"        </section>\n"
    b"      </component>\n"
    b"    </structuredBody>\n"
    b"  </component>\n"
    b"</ClinicalDocument>\n"
)


def build_submission(patient_id: str) -> DocumentSubmission:
    """Build the DocumentSubmission model for our test document."""
    return DocumentSubmission(
        patient_id=patient_id,
        document_id=TEST_DOCUMENT_ID,
        title="bidir_test_summary.xml",
        mime_type=MimeType.XML,
        creation_time="2020-01-01T12:30:00Z",
        format_code="urn:ihe:pcc:xphr:2007",
        class_code="11369-6",
        type_code="11369-6",
        service_start_time="2020-01-01T00:00:00Z",
        service_stop_time="2020-01-01T23:59:59Z",
    )


def compare_metadata(submitted: DocumentSubmission, retrieved) -> list[str]:
    """Compare submitted document metadata against retrieved metadata.

    Returns a list of difference descriptions. Empty list means everything matched.
    """
    diffs = []

    field_map = {
        "patient_id": ("patient_id", submitted.patient_id),
        "document_id": ("document_id", submitted.document_id),
        "title": ("title", submitted.title),
        "mime_type": ("mime_type", submitted.mime_type.value),
        "format_code": ("format_code", submitted.format_code),
        "class_code": ("class_code", submitted.class_code),
        "type_code": ("type_code", submitted.type_code),
        "confidentiality_code": ("confidentiality_code", submitted.confidentiality_code),
        "healthcare_facility_type_code": (
            "healthcare_facility_type_code",
            submitted.healthcare_facility_type_code,
        ),
        "practice_setting_code": ("practice_setting_code", submitted.practice_setting_code),
    }

    for field_name, (attr_name, submitted_val) in field_map.items():
        retrieved_val = getattr(retrieved, attr_name, None)
        if retrieved_val is None:
            diffs.append(f"  {field_name}: submitted={submitted_val!r}, retrieved=None (missing)")
        elif str(retrieved_val) != str(submitted_val):
            diffs.append(
                f"  {field_name}: submitted={submitted_val!r}, retrieved={retrieved_val!r}"
            )

    return diffs


def main() -> int:
    """Run the bi-directional document submission round-trip test."""
    configure_logging()

    print("=" * 60)
    print("Bi-Directional Document Submission Round-Trip Test")
    print("=" * 60)
    print()

    # ---------------------------------------------------------------
    # Step 0: Load settings and authenticate
    # ---------------------------------------------------------------
    print("Step 0: Loading configuration and authenticating...")
    try:
        settings = ParticleSettings()
    except Exception as e:
        print(f"  FAIL: Could not load settings: {e}")
        print("  Ensure PARTICLE_CLIENT_ID, PARTICLE_CLIENT_SECRET, and")
        print("  PARTICLE_SCOPE_ID are set in environment or .env file.")
        return 1

    print(f"  API base URL: {settings.base_url}")
    print()

    try:
        with ParticleHTTPClient(settings) as client:
            patient_svc = PatientService(client)
            doc_svc = DocumentService(client)

            # -----------------------------------------------------------
            # Step 1: Register patient (idempotent -- safe to re-run)
            # -----------------------------------------------------------
            print("Step 1: Registering demo patient...")
            print(f"  External patient_id: {DEMO_PATIENT.patient_id}")
            try:
                patient_response = patient_svc.register(DEMO_PATIENT)
                print(f"  Particle patient UUID: {patient_response.particle_patient_id}")
            except ParticleValidationError as e:
                print(f"  FAIL: Validation error during registration: {e.message}")
                if e.errors:
                    for err in e.errors:
                        print(f"    - {err}")
                return 1
            print("  OK")
            print()

            # We use the external patient_id for Documents API (not the UUID)
            external_patient_id = DEMO_PATIENT.patient_id

            # -----------------------------------------------------------
            # Step 2: Submit C-CDA XML document
            # -----------------------------------------------------------
            print("Step 2: Submitting C-CDA XML document...")
            submission = build_submission(external_patient_id)
            print(f"  Document ID: {submission.document_id}")
            print(f"  Title: {submission.title}")
            print(f"  MIME type: {submission.mime_type.value}")
            print(f"  File size: {len(CCDA_XML)} bytes")

            try:
                submit_response = doc_svc.submit(submission, file_content=CCDA_XML)
                print(f"  Response document_id: {submit_response.document_id}")
                print(f"  Response patient_id: {submit_response.patient_id}")
                if submit_response.status:
                    print(f"  Response status: {submit_response.status}")
            except ParticleValidationError as e:
                print(f"  FAIL: Validation error: {e.message}")
                if e.errors:
                    for err in e.errors:
                        print(f"    - {err}")
                return 1
            print("  OK")
            print()

            # -----------------------------------------------------------
            # Step 3: List documents for patient to confirm submission
            # -----------------------------------------------------------
            print("Step 3: Listing documents for patient...")
            print(f"  Patient ID: {external_patient_id}")

            # list_by_patient handles null response (returns [] instead)
            documents = doc_svc.list_by_patient(external_patient_id)
            print(f"  Found {len(documents)} document(s)")

            found_in_list = False
            for doc in documents:
                marker = " <-- our test doc" if doc.document_id == TEST_DOCUMENT_ID else ""
                print(f"    - {doc.document_id}: {doc.title} ({doc.mime_type}){marker}")
                if doc.document_id == TEST_DOCUMENT_ID:
                    found_in_list = True

            if not found_in_list:
                print(f"  WARNING: Test document {TEST_DOCUMENT_ID} not found in list")
            else:
                print("  OK -- test document found in patient's document list")
            print()

            # -----------------------------------------------------------
            # Step 4: Retrieve the submitted document metadata
            # -----------------------------------------------------------
            print("Step 4: Retrieving submitted document metadata...")
            print(f"  Document ID: {TEST_DOCUMENT_ID}")

            try:
                retrieved = doc_svc.get(TEST_DOCUMENT_ID)
                print(f"  Retrieved document_id: {retrieved.document_id}")
                print(f"  Retrieved patient_id: {retrieved.patient_id}")
                print(f"  Retrieved title: {retrieved.title}")
                print(f"  Retrieved mime_type: {retrieved.mime_type}")
                print(f"  Retrieved creation_time: {retrieved.creation_time}")
                print(f"  Retrieved format_code: {retrieved.format_code}")
                print(f"  Retrieved class_code: {retrieved.class_code}")
                print(f"  Retrieved type_code: {retrieved.type_code}")
                print(f"  Retrieved confidentiality_code: {retrieved.confidentiality_code}")
            except ParticleNotFoundError:
                print(f"  FAIL: Document {TEST_DOCUMENT_ID} not found after submission")
                return 1
            print("  OK")
            print()

            # -----------------------------------------------------------
            # Step 5: Compare submitted vs retrieved metadata
            # -----------------------------------------------------------
            print("Step 5: Comparing submitted vs retrieved metadata...")
            diffs = compare_metadata(submission, retrieved)

            if not diffs:
                print("  All metadata fields match -- round-trip successful!")
            else:
                print(f"  Found {len(diffs)} difference(s):")
                for diff in diffs:
                    print(diff)
            print()

            # -----------------------------------------------------------
            # Step 6: Clean up -- delete the test document
            # -----------------------------------------------------------
            print("Step 6: Cleaning up -- deleting test document...")
            try:
                delete_result = doc_svc.delete(TEST_DOCUMENT_ID)
                print(f"  Delete result: {delete_result}")
            except ParticleNotFoundError:
                print(f"  Document {TEST_DOCUMENT_ID} already deleted or not found")
            except ParticleAPIError as e:
                print(f"  Warning: Delete returned error ({e.status_code}): {e.message}")
            print("  OK")
            print()

            # Verify deletion by listing again
            print("  Verifying deletion...")
            post_delete_docs = doc_svc.list_by_patient(external_patient_id)
            still_present = any(
                d.document_id == TEST_DOCUMENT_ID for d in post_delete_docs
            )
            if still_present:
                print(f"  WARNING: Document {TEST_DOCUMENT_ID} still appears in list")
            else:
                print("  Confirmed: document no longer in patient's document list")
            print()

    except ParticleAuthError as e:
        print(f"\nAUTH ERROR: {e.message}")
        print("Check your PARTICLE_CLIENT_ID, PARTICLE_CLIENT_SECRET, and PARTICLE_SCOPE_ID.")
        return 1

    except ParticleAPIError as e:
        print(f"\nAPI ERROR ({e.status_code}): {e.message}")
        if e.response_body:
            print(f"  Details: {e.response_body}")
        return 1

    except Exception as e:
        print(f"\nUNEXPECTED ERROR: {type(e).__name__}: {e}")
        return 1

    # ---------------------------------------------------------------
    # Summary
    # ---------------------------------------------------------------
    print("=" * 60)
    if not diffs:
        print("RESULT: PASS -- Bi-directional round-trip completed successfully")
    else:
        print(f"RESULT: PARTIAL -- Round-trip completed with {len(diffs)} metadata difference(s)")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
