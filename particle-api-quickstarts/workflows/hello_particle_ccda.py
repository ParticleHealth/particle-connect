#!/usr/bin/env python3
"""Hello Particle (CCDA): Zero-to-clinical-documents in one script.

This script runs the full Particle Health workflow end-to-end,
retrieving original CCDA XML documents instead of flat JSON:
1. Register a demo patient
2. Submit a clinical data query
3. Poll until the query completes
4. Retrieve CCDA data as a ZIP file
5. Extract and summarize the CCDA documents

Prerequisites:
    Set these environment variables (or create a .env file):
    - PARTICLE_CLIENT_ID: Your Particle client ID
    - PARTICLE_CLIENT_SECRET: Your Particle client secret
    - PARTICLE_SCOPE_ID: Your Particle scope ID

    Validate your setup first:
        python workflows/check_setup.py

Usage:
    python workflows/hello_particle_ccda.py

Notes:
    - Uses sandbox environment by default
    - Uses a fixed patient_id for idempotent re-runs
    - Query polling may take 2-5 minutes
    - CCDA ZIP is saved to the current directory
    - Extract the ZIP to view individual CCDA XML files

When to use CCDA vs Flat:
    - CCDA: You need original clinical documents, EHR interoperability,
      or document-level provenance (e.g., which hospital sent which record)
    - Flat: You need structured data for analytics, pipelines, or databases
"""

import zipfile
from io import BytesIO
from xml.etree import ElementTree

from particle.core import (
    ParticleAPIError,
    ParticleHTTPClient,
    ParticleQueryFailedError,
    ParticleQueryTimeoutError,
    ParticleSettings,
    ParticleValidationError,
    configure_logging,
)
from particle.patient import Gender, PatientRegistration, PatientService
from particle.query import PurposeOfUse, QueryService

DEMO_PATIENT = PatientRegistration(
    given_name="Elvira",
    family_name="Valadez-Nucleus",
    date_of_birth="1970-12-26",
    gender=Gender.FEMALE,
    postal_code="02215",
    address_city="Boston",
    address_state="MA",
    patient_id="hello-particle-ccda-demo",
    address_lines=[""],
    ssn="123-45-6789",
    telephone="234-567-8910",
)

# CDA namespace used in CCDA XML documents
CDA_NS = {"cda": "urn:hl7-org:v3"}


def print_ccda_summary(ccda_bytes: bytes) -> None:
    """Extract and summarize CCDA documents from a ZIP archive."""
    print("\n=== CCDA Summary ===\n")

    with zipfile.ZipFile(BytesIO(ccda_bytes)) as zf:
        xml_files = [f for f in zf.namelist() if f.endswith(".xml")]
        print(f"Documents in ZIP: {len(xml_files)}")

        for filename in xml_files:
            print(f"\n--- {filename} ---")
            with zf.open(filename) as f:
                try:
                    tree = ElementTree.parse(f)
                    root = tree.getroot()

                    # Extract document title
                    title_el = root.find("cda:title", CDA_NS)
                    if title_el is not None and title_el.text:
                        print(f"  Title: {title_el.text.strip()}")

                    # Extract document type code
                    code_el = root.find("cda:code", CDA_NS)
                    if code_el is not None:
                        display = code_el.get("displayName", "")
                        code = code_el.get("code", "")
                        if display:
                            print(f"  Type: {display} ({code})")

                    # Extract creation time
                    time_el = root.find("cda:effectiveTime", CDA_NS)
                    if time_el is not None:
                        print(f"  Date: {time_el.get('value', 'Unknown')}")

                    # Extract custodian (sending organization)
                    custodian_name = root.find(
                        "cda:custodian/cda:assignedCustodian/"
                        "cda:representedCustodianOrganization/cda:name",
                        CDA_NS,
                    )
                    if custodian_name is not None and custodian_name.text:
                        print(f"  Custodian: {custodian_name.text.strip()}")

                    # Count sections
                    body = root.find("cda:component/cda:structuredBody", CDA_NS)
                    if body is not None:
                        sections = body.findall("cda:component/cda:section", CDA_NS)
                        section_titles = []
                        for section in sections:
                            sec_title = section.find("cda:title", CDA_NS)
                            if sec_title is not None and sec_title.text:
                                section_titles.append(sec_title.text.strip())
                        print(f"  Sections ({len(sections)}):")
                        for st in section_titles[:10]:
                            print(f"    - {st}")
                        if len(section_titles) > 10:
                            print(f"    ... and {len(section_titles) - 10} more")

                except ElementTree.ParseError:
                    print("  (Could not parse XML)")


def main() -> None:
    """Run the full CCDA retrieval workflow."""
    configure_logging()

    print("=== Hello Particle (CCDA) ===\n")

    settings = ParticleSettings()
    print(f"API: {settings.base_url}\n")

    try:
        with ParticleHTTPClient(settings) as client:
            patient_svc = PatientService(client)
            query_svc = QueryService(client)

            # Step 1: Register patient
            print("1. Registering demo patient...")
            response = patient_svc.register(DEMO_PATIENT)
            patient_id = response.particle_patient_id
            print(f"   Patient ID: {patient_id}")

            # Step 2: Submit query
            print("\n2. Submitting clinical data query...")
            query_svc.submit_query(
                particle_patient_id=patient_id,
                purpose_of_use=PurposeOfUse.TREATMENT,
            )
            print("   Query submitted")

            # Step 3: Poll for completion
            print("\n3. Waiting for query to complete (this may take 2-5 minutes)...")
            result = query_svc.wait_for_query_complete(
                particle_patient_id=patient_id,
                timeout_seconds=300,
            )
            print(f"   Status: {result.query_status.value}")
            if result.files_available:
                print(f"   Files available: {result.files_available}")

            # Step 4: Retrieve CCDA data
            print("\n4. Retrieving CCDA data...")
            ccda_bytes = query_svc.get_ccda(patient_id)

            if not ccda_bytes:
                print("\n   No CCDA data available for this patient.")
                print("   This can happen when sources only return FHIR/Flat data.")
                return

            # Save ZIP to disk
            filename = "ccda_data.zip"
            with open(filename, "wb") as f:
                f.write(ccda_bytes)
            print(f"   Saved to: {filename} ({len(ccda_bytes):,} bytes)")

            # Step 5: Summarize contents
            print_ccda_summary(ccda_bytes)

            print("\n=== Done! ===")
            print(f"\nExtract the documents:  unzip {filename}")
            print("\nNext steps:")
            print(f"  python workflows/retrieve_data.py {patient_id} flat   # compare with flat data")
            print(f"  python workflows/retrieve_data.py {patient_id} ccda   # re-download CCDA")

    except ParticleValidationError as e:
        print(f"\nValidation error: {e.message}")
        if e.errors:
            for error in e.errors:
                print(f"  - {error}")

    except ParticleQueryTimeoutError as e:
        print(f"\nQuery timed out: {e.message}")
        print("  The query is still running. Try retrieve_data.py in a few minutes:")
        print(f"  python workflows/retrieve_data.py {e.patient_id} ccda")

    except ParticleQueryFailedError as e:
        print(f"\nQuery failed: {e.message}")
        if e.error_message:
            print(f"  Details: {e.error_message}")

    except ParticleAPIError as e:
        print(f"\nAPI error ({e.status_code}): {e.message}")
        if e.response_body:
            print(f"  Details: {e.response_body}")


if __name__ == "__main__":
    main()
