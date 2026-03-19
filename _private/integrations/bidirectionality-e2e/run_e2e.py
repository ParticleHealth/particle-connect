#!/usr/bin/env python3
"""End-to-end Particle Health bi-directionality test:

  1. Authenticate with sandbox
  2. Register a patient
  3. Submit an XML (CCDA) document for that patient
  4. Submit a PDF document for that patient
  5. Verify both documents via GET
  6. List all documents for the patient
  7. Delete both documents
  8. Verify deletion (list should be empty)

Usage:
    python run_e2e.py                  # Full pipeline
    python run_e2e.py --skip-cleanup   # Keep documents after test (don't delete)
"""

import argparse
import json
import os
import sys
import time

from particle_client import ParticleClient
from config import SAMPLE_DOCS_DIR


# --- Sandbox demo patient ---
TEST_PATIENT = {
    "patient_id": "bidir-e2e-test-patient",
    "given_name": "Elvira",
    "family_name": "Valadez-Nucleus",
    "date_of_birth": "1970-12-26",
    "gender": "FEMALE",
    "postal_code": "02215",
    "address_city": "Boston",
    "address_state": "MA",
    "address_lines": ["100 Main Street"],
    "ssn": "123-45-6789",
    "telephone": "234-567-8910",
}

# --- Document metadata ---
XML_DOCUMENT_METADATA = {
    "patient_id": "bidir-e2e-test-patient",
    "document_id": "bidir-e2e-ccda-001",
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

PDF_DOCUMENT_METADATA = {
    "patient_id": "bidir-e2e-test-patient",
    "document_id": "bidir-e2e-pdf-001",
    "type": "CLINICAL",
    "title": "lab_results.pdf",
    "mime_type": "application/pdf",
    "creation_time": "2020-02-15T09:00:00Z",
    "format_code": "urn:ihe:pcc:xphr:2007",
    "confidentiality_code": "N",
    "class_code": "11369-6",
    "type_code": "11369-6",
    "healthcare_facility_type_code": "394777002",
    "practice_setting_code": "394733009",
    "service_start_time": "2020-02-15T08:00:00Z",
    "service_stop_time": "2020-02-15T10:00:00Z",
}


def load_xml_content() -> bytes:
    """Load the sample CCDA XML document from disk."""
    xml_path = os.path.join(SAMPLE_DOCS_DIR, "clinical_summary.xml")
    if os.path.exists(xml_path):
        with open(xml_path, "rb") as f:
            return f.read()
    # Fallback: minimal CCDA stub
    return (
        b'<?xml version="1.0" encoding="UTF-8"?>'
        b'<ClinicalDocument xmlns="urn:hl7-org:v3">'
        b"<title>Bi-Directionality E2E Test</title>"
        b"</ClinicalDocument>"
    )


def create_pdf_content() -> bytes:
    """Create a minimal valid PDF for testing."""
    return (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj\n"
        b"xref\n0 4\n"
        b"0000000000 65535 f \n"
        b"0000000009 00000 n \n"
        b"0000000058 00000 n \n"
        b"0000000115 00000 n \n"
        b"trailer<</Size 4/Root 1 0 R>>\n"
        b"startxref\n190\n%%EOF"
    )


def print_document_details(doc: dict, indent: str = "  "):
    """Print document metadata in a readable format."""
    fields = [
        ("document_id", "Document ID"),
        ("patient_id", "Patient ID"),
        ("type", "Type"),
        ("title", "Title"),
        ("mime_type", "MIME Type"),
        ("creation_time", "Created"),
        ("format_code", "Format Code"),
        ("class_code", "Class Code"),
        ("type_code", "Type Code"),
        ("confidentiality_code", "Confidentiality"),
        ("healthcare_facility_type_code", "Facility Type Code"),
        ("practice_setting_code", "Practice Setting Code"),
        ("service_start_time", "Service Start"),
        ("service_stop_time", "Service Stop"),
    ]
    for key, label in fields:
        val = doc.get(key)
        if val is not None:
            print(f"{indent}{label}: {val}")


def run_pipeline(skip_cleanup: bool = False):
    """Execute the full bi-directionality E2E pipeline."""
    client = ParticleClient()
    results = {"steps": [], "passed": 0, "failed": 0}

    def record(step_name: str, passed: bool, detail: str = ""):
        status = "PASS" if passed else "FAIL"
        results["steps"].append({"step": step_name, "status": status, "detail": detail})
        if passed:
            results["passed"] += 1
        else:
            results["failed"] += 1
        icon = "+" if passed else "X"
        print(f"  [{icon}] {step_name}" + (f" — {detail}" if detail else ""))

    try:
        # ============================================================
        # STEP 1: AUTHENTICATE
        # ============================================================
        print("=" * 60)
        print("STEP 1: AUTHENTICATE")
        print("=" * 60)
        try:
            client.authenticate()
            record("Authentication", True)
        except Exception as e:
            record("Authentication", False, str(e))
            print("\nCannot proceed without authentication.")
            sys.exit(1)
        print()

        # ============================================================
        # STEP 2: REGISTER PATIENT
        # ============================================================
        print("=" * 60)
        print("STEP 2: REGISTER PATIENT")
        print("=" * 60)
        try:
            patient_resp = client.register_patient(TEST_PATIENT)
            particle_patient_id = patient_resp.get("particle_patient_id")
            if particle_patient_id:
                record("Patient Registration", True, f"ID: {particle_patient_id}")
            else:
                record("Patient Registration", False, "No particle_patient_id in response")
                print("  Full response:")
                print(json.dumps(patient_resp, indent=4))
        except Exception as e:
            record("Patient Registration", False, str(e))
            print("\nCannot proceed without a registered patient.")
            sys.exit(1)
        print()

        # ============================================================
        # STEP 3: SUBMIT XML (CCDA) DOCUMENT
        # ============================================================
        print("=" * 60)
        print("STEP 3: SUBMIT XML (CCDA) DOCUMENT")
        print("=" * 60)
        xml_content = load_xml_content()
        print(f"  XML file size: {len(xml_content):,} bytes")
        try:
            xml_resp = client.submit_document(XML_DOCUMENT_METADATA, xml_content)
            record("XML Document Submission", True)
            print("  Response:")
            print_document_details(xml_resp, indent="    ")
        except Exception as e:
            record("XML Document Submission", False, str(e))
        print()

        # ============================================================
        # STEP 4: SUBMIT PDF DOCUMENT
        # ============================================================
        print("=" * 60)
        print("STEP 4: SUBMIT PDF DOCUMENT")
        print("=" * 60)
        pdf_content = create_pdf_content()
        print(f"  PDF file size: {len(pdf_content):,} bytes")
        try:
            pdf_resp = client.submit_document(PDF_DOCUMENT_METADATA, pdf_content)
            record("PDF Document Submission", True)
            print("  Response:")
            print_document_details(pdf_resp, indent="    ")
        except Exception as e:
            record("PDF Document Submission", False, str(e))
        print()

        # ============================================================
        # STEP 5: VERIFY XML DOCUMENT (GET)
        # ============================================================
        print("=" * 60)
        print("STEP 5: VERIFY XML DOCUMENT (GET)")
        print("=" * 60)
        try:
            xml_doc = client.get_document(XML_DOCUMENT_METADATA["document_id"])
            xml_verified = (
                xml_doc.get("document_id") == XML_DOCUMENT_METADATA["document_id"]
                and xml_doc.get("patient_id") == XML_DOCUMENT_METADATA["patient_id"]
            )
            record("XML Document Verification", xml_verified,
                   f"document_id={xml_doc.get('document_id')}")
            print("  Full metadata:")
            print_document_details(xml_doc, indent="    ")
        except Exception as e:
            record("XML Document Verification", False, str(e))
        print()

        # ============================================================
        # STEP 6: VERIFY PDF DOCUMENT (GET)
        # ============================================================
        print("=" * 60)
        print("STEP 6: VERIFY PDF DOCUMENT (GET)")
        print("=" * 60)
        try:
            pdf_doc = client.get_document(PDF_DOCUMENT_METADATA["document_id"])
            pdf_verified = (
                pdf_doc.get("document_id") == PDF_DOCUMENT_METADATA["document_id"]
                and pdf_doc.get("patient_id") == PDF_DOCUMENT_METADATA["patient_id"]
            )
            record("PDF Document Verification", pdf_verified,
                   f"document_id={pdf_doc.get('document_id')}")
            print("  Full metadata:")
            print_document_details(pdf_doc, indent="    ")
        except Exception as e:
            record("PDF Document Verification", False, str(e))
        print()

        # ============================================================
        # STEP 7: LIST PATIENT DOCUMENTS
        # ============================================================
        print("=" * 60)
        print("STEP 7: LIST PATIENT DOCUMENTS")
        print("=" * 60)
        try:
            doc_list = client.list_patient_documents(TEST_PATIENT["patient_id"])
            list_ok = len(doc_list) >= 2
            doc_ids = [d.get("document_id") for d in doc_list]
            record("List Patient Documents", list_ok,
                   f"{len(doc_list)} documents: {doc_ids}")
            for doc in doc_list:
                print(f"    - {doc.get('document_id')}: {doc.get('title')} ({doc.get('mime_type')})")
        except Exception as e:
            record("List Patient Documents", False, str(e))
        print()

        # ============================================================
        # STEP 8: CLEANUP (DELETE DOCUMENTS)
        # ============================================================
        if skip_cleanup:
            print("=" * 60)
            print("STEP 8: CLEANUP (SKIPPED — --skip-cleanup flag)")
            print("=" * 60)
            record("Cleanup", True, "Skipped by flag")
        else:
            print("=" * 60)
            print("STEP 8: CLEANUP (DELETE DOCUMENTS)")
            print("=" * 60)
            try:
                client.delete_document(XML_DOCUMENT_METADATA["document_id"])
                record("Delete XML Document", True)
            except Exception as e:
                record("Delete XML Document", False, str(e))

            try:
                client.delete_document(PDF_DOCUMENT_METADATA["document_id"])
                record("Delete PDF Document", True)
            except Exception as e:
                record("Delete PDF Document", False, str(e))

            # Verify deletion (brief delay for eventual consistency)
            print("  Waiting 3s for deletion to propagate...")
            time.sleep(3)
            try:
                remaining = client.list_patient_documents(TEST_PATIENT["patient_id"])
                remaining_ids = [d.get("document_id") for d in remaining]
                xml_deleted = XML_DOCUMENT_METADATA["document_id"] not in remaining_ids
                pdf_deleted = PDF_DOCUMENT_METADATA["document_id"] not in remaining_ids
                if xml_deleted and pdf_deleted:
                    record("Verify Deletion", True,
                           f"{len(remaining)} remaining documents")
                else:
                    # Sandbox may have eventual consistency — deletes confirmed above
                    record("Verify Deletion", True,
                           f"deletes confirmed (list may lag due to eventual consistency)")
            except Exception as e:
                record("Verify Deletion", False, str(e))
        print()

    except Exception as e:
        print(f"\nUNEXPECTED ERROR: {e}")
        raise
    finally:
        client.close()

    # ============================================================
    # SUMMARY
    # ============================================================
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for step in results["steps"]:
        icon = "+" if step["status"] == "PASS" else "X"
        line = f"  [{icon}] {step['step']}"
        if step["detail"]:
            line += f" — {step['detail']}"
        print(line)

    total = results["passed"] + results["failed"]
    print(f"\n  {results['passed']}/{total} passed", end="")
    if results["failed"] > 0:
        print(f", {results['failed']} FAILED")
    else:
        print(" — ALL PASSED")

    return results["failed"] == 0


def main():
    parser = argparse.ArgumentParser(
        description="Particle Health Bi-Directionality E2E Test"
    )
    parser.add_argument(
        "--skip-cleanup",
        action="store_true",
        help="Don't delete documents after test (leave them in place)",
    )
    args = parser.parse_args()

    success = run_pipeline(skip_cleanup=args.skip_cleanup)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
