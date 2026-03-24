#!/usr/bin/env python3
"""FHIR R4 E2E Test: Register, query, retrieve, and parse as FHIR R4 Bundle.

This script demonstrates a Particle Health workflow that produces FHIR R4 output:
1. Authenticate with the Particle sandbox API (via SDK)
2. Register the sandbox test patient (Elvira Valadez-Nucleus)
3. Submit a clinical data query and wait for completion with exponential backoff
4. Retrieve patient data and construct FHIR R4 Bundle resources
5. Parse the FHIR Bundle and extract: Patient, Condition, and MedicationStatement
6. Print a summary of each resource type with count and key fields

IMPORTANT — Sandbox limitation:
    The Particle FHIR endpoint (GET /api/v2/patients/{id}/fhir) returns 404 in
    sandbox. FHIR is production-only. This script retrieves flat JSON data from
    the sandbox and converts it to FHIR R4 Bundle format client-side, giving you
    real clinical data in the FHIR R4 structure you need.

    In production, replace the flat-to-FHIR conversion with:
        fhir_bundle = query_svc.get_fhir(particle_patient_id)

Prerequisites:
    Set these environment variables (or create a .env file in particle-api-quickstarts/):
    - PARTICLE_CLIENT_ID
    - PARTICLE_CLIENT_SECRET
    - PARTICLE_SCOPE_ID

Usage:
    cd particle-api-quickstarts
    source .venv/bin/activate
    python ../_private/feedback-e2e-tests/output/test4_fhir.py
"""

import json
import sys
import uuid
from datetime import datetime

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

# Sandbox test patient — the only patient that returns flat data in sandbox.
# Demographics from hello_particle.py and SDK documentation.
DEMO_PATIENT = PatientRegistration(
    given_name="Elvira",
    family_name="Valadez-Nucleus",
    date_of_birth="1970-12-26",
    gender=Gender.FEMALE,
    postal_code="02215",
    address_city="Boston",
    address_state="MA",  # Two-letter abbreviation required
    patient_id="test4-fhir-e2e",
    address_lines=[""],
    ssn="123-45-6789",
    telephone="234-567-8910",
)


# ---------------------------------------------------------------------------
# Flat-to-FHIR R4 conversion
# ---------------------------------------------------------------------------


def flat_to_fhir_bundle(flat_data: dict, particle_patient_id: str) -> dict:
    """Convert Particle flat JSON data into a FHIR R4 Bundle.

    Builds a searchset Bundle containing:
    - One Patient resource from the "patients" array
    - Condition resources from the "problems" array
    - MedicationStatement resources from the "medications" array

    This is a pragmatic mapping for sandbox use. In production, call
    query_svc.get_fhir() to get a server-generated FHIR Bundle directly.

    Args:
        flat_data: Flat JSON dict from QueryService.get_flat()
        particle_patient_id: Particle's UUID for the patient

    Returns:
        FHIR R4 Bundle dict
    """
    entries = []

    # --- Patient resource ---
    patients = flat_data.get("patients", [])
    patient_resource = _build_patient_resource(
        patients[0] if patients else {}, particle_patient_id
    )
    entries.append({
        "fullUrl": f"urn:uuid:{patient_resource['id']}",
        "resource": patient_resource,
        "search": {"mode": "match"},
    })

    # --- Condition resources (from "problems") ---
    problems = flat_data.get("problems", [])
    for i, problem in enumerate(problems):
        condition = _build_condition_resource(problem, patient_resource["id"], i)
        entries.append({
            "fullUrl": f"urn:uuid:{condition['id']}",
            "resource": condition,
            "search": {"mode": "match"},
        })

    # --- MedicationStatement resources (from "medications") ---
    medications = flat_data.get("medications", [])
    for i, med in enumerate(medications):
        med_stmt = _build_medication_statement_resource(
            med, patient_resource["id"], i
        )
        entries.append({
            "fullUrl": f"urn:uuid:{med_stmt['id']}",
            "resource": med_stmt,
            "search": {"mode": "match"},
        })

    bundle = {
        "resourceType": "Bundle",
        "id": str(uuid.uuid4()),
        "type": "searchset",
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total": len(entries),
        "entry": entries,
    }

    return bundle


def _build_patient_resource(patient_flat: dict, particle_patient_id: str) -> dict:
    """Map flat patient record to FHIR R4 Patient resource."""
    resource = {
        "resourceType": "Patient",
        "id": particle_patient_id,
        "identifier": [
            {
                "system": "https://particlehealth.com/patient-id",
                "value": particle_patient_id,
            }
        ],
    }

    # Name
    given = patient_flat.get("given_name", "")
    family = patient_flat.get("family_name", "")
    if given or family:
        name_entry = {"use": "official"}
        if family:
            name_entry["family"] = family
        if given:
            name_entry["given"] = [given]
        resource["name"] = [name_entry]

    # Gender
    gender_raw = patient_flat.get("gender", "")
    if gender_raw:
        resource["gender"] = gender_raw.lower()

    # Birth date
    dob = patient_flat.get("date_of_birth", "")
    if dob:
        resource["birthDate"] = dob

    # Address
    city = patient_flat.get("address_city", "")
    state = patient_flat.get("address_state", "")
    postal = patient_flat.get("postal_code", "")
    if city or state or postal:
        addr = {}
        if city:
            addr["city"] = city
        if state:
            addr["state"] = state
        if postal:
            addr["postalCode"] = postal
        resource["address"] = [addr]

    # Phone
    phone = patient_flat.get("telephone", "")
    if phone:
        resource["telecom"] = [{"system": "phone", "value": phone}]

    return resource


def _build_condition_resource(
    problem: dict, patient_id: str, index: int
) -> dict:
    """Map flat problem record to FHIR R4 Condition resource."""
    resource = {
        "resourceType": "Condition",
        "id": str(uuid.uuid4()),
        "subject": {"reference": f"Patient/{patient_id}"},
    }

    # Code
    condition_name = problem.get("condition_name", "")
    condition_code = problem.get("condition_code", "")
    condition_system = problem.get("condition_code_system", "")
    if condition_name or condition_code:
        coding = {}
        if condition_code:
            coding["code"] = condition_code
        if condition_system:
            coding["system"] = condition_system
        if condition_name:
            coding["display"] = condition_name
        resource["code"] = {
            "coding": [coding] if coding else [],
            "text": condition_name,
        }

    # Clinical status
    clinical_status = problem.get("condition_clinical_status", "")
    if clinical_status:
        resource["clinicalStatus"] = {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                    "code": clinical_status.lower(),
                }
            ]
        }

    # Verification status
    verification_status = problem.get("condition_verification_status", "")
    if verification_status:
        resource["verificationStatus"] = {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                    "code": verification_status.lower(),
                }
            ]
        }

    # Onset
    onset = problem.get("condition_onset_date", "")
    if onset:
        resource["onsetDateTime"] = onset

    # Category
    category = problem.get("condition_category", "")
    if category:
        resource["category"] = [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-category",
                        "code": category.lower().replace(" ", "-"),
                        "display": category,
                    }
                ]
            }
        ]

    return resource


def _build_medication_statement_resource(
    med: dict, patient_id: str, index: int
) -> dict:
    """Map flat medication record to FHIR R4 MedicationStatement resource."""
    resource = {
        "resourceType": "MedicationStatement",
        "id": str(uuid.uuid4()),
        "subject": {"reference": f"Patient/{patient_id}"},
    }

    # Status (FHIR MedicationStatement requires status)
    status_raw = med.get("medication_statement_status", "")
    if status_raw:
        resource["status"] = status_raw.lower()
    else:
        resource["status"] = "unknown"

    # Medication
    med_name = med.get("medication_name", "")
    med_code = med.get("medication_code", "")
    med_system = med.get("medication_code_system", "")
    if med_name or med_code:
        coding = {}
        if med_code:
            coding["code"] = med_code
        if med_system:
            coding["system"] = med_system
        if med_name:
            coding["display"] = med_name
        resource["medicationCodeableConcept"] = {
            "coding": [coding] if coding else [],
            "text": med_name,
        }

    # Dosage
    route = med.get("medication_statement_dose_route", "")
    dose_value = med.get("medication_statement_dose_value", "")
    dose_unit = med.get("medication_statement_dose_unit", "")
    if route or dose_value or dose_unit:
        dosage = {}
        if route:
            dosage["route"] = {"text": route}
        if dose_value or dose_unit:
            dose_quantity = {}
            if dose_value:
                try:
                    dose_quantity["value"] = float(dose_value)
                except ValueError:
                    dose_quantity["value"] = dose_value
            if dose_unit:
                dose_quantity["unit"] = dose_unit
            dosage["doseAndRate"] = [{"doseQuantity": dose_quantity}]
        resource["dosage"] = [dosage]

    # Effective period
    start = med.get("medication_statement_start_date", "")
    end = med.get("medication_statement_end_date", "")
    if start or end:
        period = {}
        if start:
            period["start"] = start
        if end:
            period["end"] = end
        resource["effectivePeriod"] = period

    return resource


# ---------------------------------------------------------------------------
# FHIR Bundle parsing and summary
# ---------------------------------------------------------------------------


def parse_fhir_bundle(bundle: dict) -> dict:
    """Parse a FHIR R4 Bundle and group resources by type.

    Args:
        bundle: FHIR R4 Bundle dict

    Returns:
        Dict mapping resourceType -> list of resources
    """
    resources_by_type = {}
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        rtype = resource.get("resourceType", "Unknown")
        resources_by_type.setdefault(rtype, []).append(resource)
    return resources_by_type


def print_bundle_summary(bundle: dict) -> None:
    """Print a detailed summary of the FHIR R4 Bundle contents."""
    print("\n=== FHIR R4 Bundle Summary ===\n")
    print(f"  Bundle ID:    {bundle.get('id', 'N/A')}")
    print(f"  Bundle Type:  {bundle.get('type', 'N/A')}")
    print(f"  Timestamp:    {bundle.get('timestamp', 'N/A')}")
    print(f"  Total:        {bundle.get('total', 0)} entries")

    resources = parse_fhir_bundle(bundle)

    # Overview
    print("\n--- Resource Type Counts ---\n")
    print(f"  {'Resource Type':<30} {'Count':>6}")
    print(f"  {'-' * 30} {'-' * 6}")
    for rtype, items in sorted(resources.items()):
        print(f"  {rtype:<30} {len(items):>6}")

    # Patient details
    patients = resources.get("Patient", [])
    if patients:
        print(f"\n--- Patient Resources ({len(patients)}) ---\n")
        for patient in patients:
            names = patient.get("name", [])
            name_str = "Unknown"
            if names:
                given = " ".join(names[0].get("given", []))
                family = names[0].get("family", "")
                name_str = f"{given} {family}".strip()
            gender = patient.get("gender", "N/A")
            dob = patient.get("birthDate", "N/A")
            patient_id = patient.get("id", "N/A")

            print(f"  Name:      {name_str}")
            print(f"  Gender:    {gender}")
            print(f"  DOB:       {dob}")
            print(f"  ID:        {patient_id}")

            addresses = patient.get("address", [])
            if addresses:
                addr = addresses[0]
                parts = [
                    addr.get("city", ""),
                    addr.get("state", ""),
                    addr.get("postalCode", ""),
                ]
                print(f"  Address:   {', '.join(p for p in parts if p)}")

            telecoms = patient.get("telecom", [])
            for tc in telecoms:
                print(f"  {tc.get('system', 'contact').title()}: {tc.get('value', 'N/A')}")

    # Condition details
    conditions = resources.get("Condition", [])
    if conditions:
        print(f"\n--- Condition Resources ({len(conditions)}) ---\n")
        print(f"  {'Condition Name':<50} {'Status':<15} {'Onset':<12}")
        print(f"  {'-' * 50} {'-' * 15} {'-' * 12}")
        for cond in conditions:
            code = cond.get("code", {})
            name = code.get("text", "")
            if not name:
                codings = code.get("coding", [])
                name = codings[0].get("display", "Unknown") if codings else "Unknown"
            name = name[:50]

            cs = cond.get("clinicalStatus", {})
            status_codings = cs.get("coding", [])
            status = status_codings[0].get("code", "N/A") if status_codings else "N/A"

            onset = cond.get("onsetDateTime", "N/A")

            print(f"  {name:<50} {status:<15} {onset:<12}")

    # MedicationStatement details
    med_stmts = resources.get("MedicationStatement", [])
    if med_stmts:
        print(f"\n--- MedicationStatement Resources ({len(med_stmts)}) ---\n")
        print(f"  {'Medication Name':<50} {'Status':<12} {'Route':<15}")
        print(f"  {'-' * 50} {'-' * 12} {'-' * 15}")
        for ms in med_stmts:
            med_cc = ms.get("medicationCodeableConcept", {})
            name = med_cc.get("text", "")
            if not name:
                codings = med_cc.get("coding", [])
                name = codings[0].get("display", "Unknown") if codings else "Unknown"
            name = name[:50]

            status = ms.get("status", "N/A")

            route = ""
            dosages = ms.get("dosage", [])
            if dosages:
                route = dosages[0].get("route", {}).get("text", "")

            print(f"  {name:<50} {status:<12} {route:<15}")


# ---------------------------------------------------------------------------
# Main workflow
# ---------------------------------------------------------------------------


def retrieve_and_convert(settings: ParticleSettings) -> dict:
    """Authenticate, register patient, query, retrieve flat data, convert to FHIR R4.

    Returns:
        FHIR R4 Bundle dict
    """
    print("=== Particle FHIR R4 Integration ===\n")
    print(f"API: {settings.base_url}")

    is_sandbox = "sandbox" in settings.base_url
    if is_sandbox:
        print("Environment: sandbox (FHIR endpoint unavailable -- using flat-to-FHIR conversion)")
    else:
        print("Environment: production (native FHIR endpoint available)")
    print()

    with ParticleHTTPClient(settings) as client:
        patient_svc = PatientService(client)
        query_svc = QueryService(client)

        # Step 1: Register patient
        print("1. Registering sandbox test patient...")
        response = patient_svc.register(DEMO_PATIENT)
        particle_patient_id = response.particle_patient_id
        print(f"   Particle Patient ID: {particle_patient_id}")

        # Step 2: Submit query
        print("\n2. Submitting clinical data query...")
        query_svc.submit_query(
            particle_patient_id=particle_patient_id,
            purpose_of_use=PurposeOfUse.TREATMENT,
        )
        print("   Query submitted")

        # Step 3: Wait for completion (SDK uses exponential backoff automatically)
        print("\n3. Waiting for query to complete (may take 2-5 minutes)...")
        result = query_svc.wait_for_query_complete(
            particle_patient_id=particle_patient_id,
            timeout_seconds=300,
        )
        print(f"   Status: {result.query_status.value}")
        if result.files_available:
            print(f"   Files available: {result.files_available}")

        # Step 4: Retrieve data and build FHIR Bundle
        if is_sandbox:
            # Sandbox: FHIR endpoint returns 404, so retrieve flat data and convert
            print("\n4. Retrieving flat data (sandbox does not support FHIR endpoint)...")
            flat_data = query_svc.get_flat(particle_patient_id)

            resource_types = [
                k for k, v in flat_data.items() if isinstance(v, list)
            ]
            print(f"   Flat data resource types: {len(resource_types)}")

            print("\n5. Converting flat data to FHIR R4 Bundle...")
            bundle = flat_to_fhir_bundle(flat_data, particle_patient_id)
            print(f"   Bundle entries: {bundle['total']}")
        else:
            # Production: use native FHIR endpoint
            print("\n4. Retrieving FHIR R4 Bundle from Particle...")
            bundle = query_svc.get_fhir(particle_patient_id)
            print(f"   Bundle entries: {bundle.get('total', len(bundle.get('entry', [])))}")

        return bundle


def main() -> None:
    """Run the full FHIR R4 E2E test."""
    configure_logging()

    try:
        settings = ParticleSettings()
        bundle = retrieve_and_convert(settings)

        if not bundle.get("entry"):
            print("\nNo data in FHIR Bundle. Sandbox only returns data for seeded test patients.")
            sys.exit(1)

        # Parse and display the FHIR Bundle
        print_bundle_summary(bundle)

        # Validate structure
        resources = parse_fhir_bundle(bundle)
        patient_count = len(resources.get("Patient", []))
        condition_count = len(resources.get("Condition", []))
        med_stmt_count = len(resources.get("MedicationStatement", []))

        print("\n=== Validation ===\n")
        print(f"  Patient resources:            {patient_count}")
        print(f"  Condition resources:           {condition_count}")
        print(f"  MedicationStatement resources: {med_stmt_count}")

        assert patient_count >= 1, "Expected at least 1 Patient resource"
        print("\n  All checks passed.")
        print("\n=== Done! ===")

    except ParticleValidationError as e:
        print(f"\nValidation error: {e.message}")
        if e.errors:
            for error in e.errors:
                print(f"  - {error}")
        sys.exit(1)

    except ParticleQueryTimeoutError as e:
        print(f"\nQuery timed out: {e.message}")
        print("  The query may still be processing. Try again later.")
        sys.exit(1)

    except ParticleQueryFailedError as e:
        print(f"\nQuery failed: {e.message}")
        if e.error_message:
            print(f"  Details: {e.error_message}")
        sys.exit(1)

    except ParticleAPIError as e:
        print(f"\nAPI error ({e.status_code}): {e.message}")
        if e.response_body:
            print(f"  Details: {e.response_body}")
        sys.exit(1)


if __name__ == "__main__":
    main()
